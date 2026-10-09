import os
import uuid
from datetime import datetime
from PIL import Image

import boto3
from botocore.client import Config
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt

from .models import Document, Department, Workflow, ImageAttachment
from .services.render_markdown import render_markdown
from .services.extract_text import extract_html_plain_text

def get_s3_client():
    """Tạo client kết nối S3 Gateway của SeaweedFS"""
    return boto3.client(
        's3',
        endpoint_url=settings.SEAWEEDFS_S3_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4')
    )


def doc_list(request):
    """Trang chủ danh sách quy trình: Chỉ hiển thị bài PUBLISHED cho người xem công cộng"""
    query = request.GET.get('q', '').strip()
    selected_dept = request.GET.get('department', '').strip()
    selected_flow = request.GET.get('flow', '').strip()

    # Viewer chỉ thấy bài PUBLISHED; Admin đăng nhập có thể thấy cả bài DRAFT
    if request.user.is_authenticated and request.user.is_staff:
        documents = Document.objects.all()
    else:
        documents = Document.published.all()

    documents = documents.select_related('department', 'workflow', 'author')

    # Lọc bộ môn
    if selected_dept:
        documents = documents.filter(department__code=selected_dept)

    # Lọc luồng công việc
    if selected_flow:
        documents = documents.filter(workflow__slug=selected_flow)

    # Tìm kiếm toàn văn
    if query:
        documents = documents.filter(
            Q(code__icontains=query) |
            Q(title__icontains=query) |
            Q(search_text__icontains=query)
        )

    departments = Department.objects.prefetch_related('documents').all()
    workflows = Workflow.objects.all()

    context = {
        'documents': documents,
        'departments': departments,
        'workflows': workflows,
        'query': query,
        'selected_dept': selected_dept,
        'selected_flow': selected_flow,
        'total_count': documents.count(),
    }
    return render(request, 'docs/list.html', context)


def find_document_by_slug_or_code(slug, qs):
    """Tìm kiếm linh hoạt theo slug chính xác, mã code, hoặc tiền tố mã để chống lỗi 404 khi đổi tiêu đề"""
    doc = qs.filter(slug=slug).first()
    if doc:
        return doc
    doc = qs.filter(code__iexact=slug).first()
    if doc:
        return doc
    parts = slug.split('-')
    if len(parts) >= 3:
        possible_code = f"{parts[0]}-{parts[1]}-{parts[2]}"
        doc = qs.filter(code__iexact=possible_code).first()
        if doc:
            return doc
    if len(parts) >= 2:
        possible_code = f"{parts[0]}-{parts[1]}"
        doc = qs.filter(code__iexact=possible_code).first()
        if doc:
            return doc
    doc = qs.filter(slug__istartswith=slug[:35]).first()
    if doc:
        return doc
    return None


def doc_detail(request, slug):
    """Trang chi tiết quy trình: Hỗ trợ Markdown + Auto TOC hoặc File HTML độc lập trong iframe sandbox"""
    qs = Document.objects.select_related('department', 'workflow', 'author')
    if not (request.user.is_authenticated and request.user.is_staff):
        qs = Document.published.select_related('department', 'workflow', 'author')

    doc = find_document_by_slug_or_code(slug, qs)
    if not doc:
        raise Http404("Không tìm thấy tài liệu quy trình")

    # Tự động nhận diện nếu bài có HTML mà markdown rỗng
    effective_is_html = (doc.content_type == 'HTML') or (bool(doc.content_html) and not bool(doc.content_markdown))

    rendered_data = {}
    if not effective_is_html and doc.content_markdown:
        rendered_data = render_markdown(doc.content_markdown)

    related_docs = Document.published.filter(
        department=doc.department
    ).exclude(pk=doc.pk)[:5]

    html_url = f"/docs/{doc.slug}/raw-html/" if doc.content_html else (f"/media/{doc.html_file}" if doc.html_file else None)

    context = {
        'doc': doc,
        'effective_is_html': effective_is_html,
        'rendered_content': rendered_data.get('html', ''),
        'toc_html': rendered_data.get('toc_html', ''),
        'toc_tokens': rendered_data.get('toc_tokens', []),
        'related_docs': related_docs,
        'html_url': html_url,
    }
    return render(request, 'docs/detail.html', context)


def doc_html_raw(request, slug):
    """
    Phục vụ trực tiếp nội dung HTML độc lập được lưu trong PostgreSQL DB.
    Kiểm soát quyền truy cập:
    - Nếu bài viết là DRAFT: Chỉ Admin/Staff mới xem được, khách ẩn danh nhận 404.
    - Cưỡng chế Sandbox CSP và Content-Type utf-8.
    """
    qs = Document.objects.all()
    if not (request.user.is_authenticated and request.user.is_staff):
        qs = Document.published.all()

    doc = find_document_by_slug_or_code(slug, qs)
    if not doc or not doc.content_html:
        raise Http404("Tài liệu không có nội dung HTML trong CSDL")

    response = HttpResponse(doc.content_html, content_type='text/html; charset=utf-8')
    response['Content-Security-Policy'] = "sandbox allow-scripts"
    response['X-Content-Type-Options'] = "nosniff"
    if doc.status == 'PUBLISHED':
        response['Cache-Control'] = 'public, max-age=3600'
    else:
        response['Cache-Control'] = 'private, no-store'
    return response


def media_access(request, path):
    """
    Cơ chế kiểm quyền file qua Nginx X-Accel-Redirect.
    Trình duyệt gọi /media/<path> -> Django kiểm tra quyền -> Nginx stream trực tiếp từ SeaweedFS.
    Ngăn chặn tuyệt đối việc lộ file hoặc ảnh của các bài DRAFT.
    """
    clean_path = path.lstrip('/')

    # 1. Nếu là Admin đăng nhập: Cho phép xem ngay (phục vụ live preview khi soạn thảo)
    if request.user.is_authenticated and request.user.is_staff:
        response = HttpResponse()
        response['X-Accel-Redirect'] = f'/_storage/{clean_path}'
        response['Cache-Control'] = 'private, no-store'
        return response

    # 2. Nếu là người xem công cộng:
    # File hợp lệ khi và chỉ khi:
    # - Là ảnh thuộc ít nhất 1 bài viết PUBLISHED
    # - HOẶC là file HTML của 1 bài viết PUBLISHED
    is_public_image = ImageAttachment.objects.filter(
        file=clean_path,
        documents__status='PUBLISHED'
    ).exists()

    is_public_html = Document.published.filter(
        html_file=clean_path
    ).exists()

    if is_public_image or is_public_html:
        response = HttpResponse()
        response['X-Accel-Redirect'] = f'/_storage/{clean_path}'
        response['Cache-Control'] = 'public, max-age=3600'
        return response

    # 3. Không có quyền -> Trả về 404 (Không trả 403 để không lộ sự tồn tại của file)
    raise Http404("Tài nguyên không tồn tại")


@csrf_exempt
@staff_member_required
def api_upload_image(request):
    """
    API tiếp nhận ảnh Paste trực tiếp (Ctrl+V) từ trình soạn thảo Admin.
    Tải thẳng lên SeaweedFS S3 qua Boto3 và lưu ImageAttachment.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Phương thức không hợp lệ'}, status=405)

    upload_file = request.FILES.get('image') or request.FILES.get('file')
    if not upload_file:
        return JsonResponse({'error': 'Không tìm thấy tệp ảnh'}, status=400)

    # Giới hạn dung lượng ≤ 10MB
    if upload_file.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'Kích thước tệp vượt quá 10MB'}, status=400)

    # Xác thực định dạng ảnh bằng Pillow
    try:
        img = Image.open(upload_file)
        img.verify()
        upload_file.seek(0)
    except Exception:
        return JsonResponse({'error': 'Tệp không phải là hình ảnh hợp lệ'}, status=400)

    # Đổi tên file UUID
    ext = os.path.splitext(upload_file.name)[1].lower() or '.png'
    if ext not in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
        ext = '.png'

    now = datetime.now()
    key = f"images/{now.year}/{now.month:02d}/{uuid.uuid4().hex}{ext}"

    try:
        s3 = get_s3_client()
        s3.upload_fileobj(
            upload_file,
            settings.AWS_STORAGE_BUCKET_NAME,
            key,
            ExtraArgs={'ContentType': f"image/{ext.lstrip('.')}"}
        )

        # Lưu bản ghi ImageAttachment (chưa liên kết bài viết, chỉ Admin xem được)
        ImageAttachment.objects.create(
            file=key,
            uploaded_by=request.user
        )

        return JsonResponse({
            'success': True,
            'url': f"/media/{key}",
            'filename': upload_file.name
        })
    except Exception as e:
        return JsonResponse({'error': f"Lỗi lưu trữ SeaweedFS S3: {str(e)}"}, status=500)


@csrf_exempt
@staff_member_required
def api_upload_html(request):
    """
    API tải lên 1 file HTML độc lập (≤ 5MB) lưu trữ lên SeaweedFS S3.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Phương thức không hợp lệ'}, status=405)

    upload_file = request.FILES.get('html_file')
    if not upload_file:
        return JsonResponse({'error': 'Không tìm thấy tệp HTML'}, status=400)

    if upload_file.size > 5 * 1024 * 1024:
        return JsonResponse({'error': 'Kích thước tệp HTML vượt quá 5MB'}, status=400)

    if not upload_file.name.lower().endswith('.html'):
        return JsonResponse({'error': 'Chỉ chấp nhận tệp có đuôi .html'}, status=400)

    try:
        raw_content = upload_file.read().decode('utf-8', errors='replace')
        upload_file.seek(0)
    except Exception:
        return JsonResponse({'error': 'Tệp không đúng định dạng mã hóa UTF-8'}, status=400)

    key = f"html/{uuid.uuid4().hex}.html"

    try:
        s3 = get_s3_client()
        s3.upload_fileobj(
            upload_file,
            settings.AWS_STORAGE_BUCKET_NAME,
            key,
            ExtraArgs={'ContentType': 'text/html; charset=utf-8'}
        )

        plain_text = extract_html_plain_text(raw_content)

        return JsonResponse({
            'success': True,
            'key': key,
            'url': f"/media/{key}",
            'plain_text': plain_text[:5000]
        })
    except Exception as e:
        return JsonResponse({'error': f"Lỗi lưu trữ SeaweedFS: {str(e)}"}, status=500)
