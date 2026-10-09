from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Department, Workflow, Document, ImageAttachment
from .services.sync_images import sync_document_images
from .services.extract_text import extract_markdown_plain_text, extract_html_plain_text

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code_badge', 'name', 'slug', 'document_count')
    search_fields = ('code', 'name')
    prepopulated_fields = {'slug': ('code',)}

    def code_badge(self, obj):
        return format_html(
            '<span style="background: #e0f2fe; color: #0369a1; font-family: monospace; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 11px; border: 1px solid #bae6fd;">{}</span>',
            obj.code
        )
    code_badge.short_description = "Mã bộ môn"

    def document_count(self, obj):
        count = obj.documents.count()
        return format_html('<span style="font-weight: 600; color: #0284c7;">{} bài quy trình</span>', count)
    document_count.short_description = "Số lượng quy trình"


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'document_count')
    list_editable = ('order',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def document_count(self, obj):
        count = obj.documents.count()
        return format_html('<span style="font-weight: 600; color: #0284c7;">{} bài quy trình</span>', count)
    document_count.short_description = "Số lượng quy trình"


@admin.register(ImageAttachment)
class ImageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_key', 'linked_documents_count', 'uploaded_by', 'uploaded_at', 'preview_btn')
    search_fields = ('file',)
    readonly_fields = ('file', 'uploaded_by', 'uploaded_at', 'linked_documents_count')

    def file_key(self, obj):
        return format_html(
            '<span style="font-family: monospace; font-size: 12px; color: #334155;">{}</span>',
            obj.file
        )
    file_key.short_description = "Đường dẫn file (S3 Key)"

    def linked_documents_count(self, obj):
        count = obj.documents.count()
        if count > 0:
            return format_html('<span style="font-weight: 600; color: #16a34a; background: #ecfdf5; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">✓ Liên kết {} bài</span>', count)
        return format_html('<span style="font-weight: 600; color: #dc2626; background: #fef2f2; padding: 2px 8px; border-radius: 9999px; font-size: 11px;">Chưa liên kết</span>')
    linked_documents_count.short_description = "Trạng thái liên kết"

    def preview_btn(self, obj):
        return format_html(
            '<a href="{}" target="_blank" style="padding: 3px 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600; color: #0284c7;">Xem ảnh ↗</a>',
            obj.url
        )
    preview_btn.short_description = "Xem tệp"


class DocumentAdminForm(forms.ModelForm):
    upload_html_file = forms.FileField(
        required=False,
        label="Tải lên tệp .html từ máy tính",
        help_text="Chọn tệp HTML độc lập (≤ 5MB) để nạp nội dung trực tiếp vào CSDL PostgreSQL.",
        widget=forms.FileInput(attrs={'accept': '.html', 'id': 'id_upload_html_file'})
    )

    class Meta:
        model = Document
        fields = '__all__'
        widgets = {
            'content_html': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Nội dung HTML được lưu trực tiếp vào CSDL PostgreSQL khi tải tệp lên hoặc nhập tại đây...',
                'style': 'font-family: monospace; font-size: 12px; width: 100%;'
            })
        }


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    form = DocumentAdminForm
    change_form_template = 'admin/docs/document/change_form.html'
    list_display = ('code_badge', 'title', 'department', 'workflow', 'content_type_badge', 'status_badge', 'updated_at')
    list_filter = ('department', 'workflow', 'content_type', 'status')
    search_fields = ('code', 'title', 'search_text', 'content_markdown', 'content_html')
    prepopulated_fields = {'slug': ('code',)}

    fieldsets = (
        ("1. Thông tin Quy trình", {
            'fields': (
                ('code', 'status'),
                'title',
                ('department', 'workflow'),
            )
        }),
        ("2. Định dạng Nội dung", {
            'description': "Chọn định dạng: Soạn thảo Markdown với Live Preview hoặc Tải lên 1 tệp HTML vào CSDL.",
            'fields': (
                'content_type',
            )
        }),
        ("3. Soạn thảo Markdown (Kèm Xem trước Trực tiếp & Paste ảnh)", {
            'classes': ('fieldset-markdown',),
            'fields': (
                'content_markdown',
            )
        }),
        ("4. Tệp HTML Độc lập (Lưu trữ trực tiếp trong CSDL)", {
            'classes': ('fieldset-html',),
            'description': "Tải lên 1 tệp HTML độc lập (Single-file). Toàn bộ nội dung tệp HTML sẽ được lưu trữ trực tiếp vào CSDL PostgreSQL.",
            'fields': (
                'upload_html_file',
                'content_html',
            )
        }),
        ("5. Cấu hình Nâng cao (Tùy chọn)", {
            'classes': ('collapse',),
            'fields': (
                ('slug', 'author'),
            )
        }),
    )

    class Media:
        css = {
            'all': (
                'css/admin_theme.css',
                'css/admin_markdown.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
            'js/admin_docs.js',
        )

    def code_badge(self, obj):
        return format_html(
            '<span style="background: #f1f5f9; color: #0f172a; font-family: monospace; font-weight: 700; padding: 2px 7px; border-radius: 4px; font-size: 11.5px; border: 1px solid #cbd5e1;">{}</span>',
            obj.code
        )
    code_badge.short_description = "Mã quy trình"

    def content_type_badge(self, obj):
        if obj.content_type == 'MARKDOWN':
            return format_html('<span style="background: #f8fafc; color: #475569; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; border: 1px solid #e2e8f0;">📝 Markdown</span>')
        return format_html('<span style="background: #eff6ff; color: #1d4ed8; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 600; border: 1px solid #bfdbfe;">📄 HTML (CSDL)</span>')
    content_type_badge.short_description = "Định dạng"

    def status_badge(self, obj):
        if obj.status == 'PUBLISHED':
            return format_html('<span style="background: #ecfdf5; color: #047857; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700; border: 1px solid #a7f3d0;">PUBLISHED</span>')
        return format_html('<span style="background: #fffbeb; color: #b45309; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700; border: 1px solid #fde68a;">DRAFT</span>')
    status_badge.short_description = "Trạng thái"

    def save_model(self, request, obj, form, change):
        if not obj.author and request.user.is_authenticated:
            obj.author = request.user

        if obj.status == 'PUBLISHED' and not obj.published_at:
            obj.published_at = timezone.now()

        # 1. Nếu người dùng chọn file HTML từ máy tính: đọc nội dung lưu thẳng vào DB
        uploaded_html = form.cleaned_data.get('upload_html_file')
        if uploaded_html:
            raw_html = uploaded_html.read().decode('utf-8', errors='replace')
            obj.content_html = raw_html
            obj.content_type = 'HTML'  # Tự động gán sang định dạng HTML
            obj.search_text = extract_html_plain_text(raw_html)
        elif obj.content_html and not obj.content_markdown:
            obj.content_type = 'HTML'
            obj.search_text = extract_html_plain_text(obj.content_html)
        elif obj.content_type == 'HTML' and obj.content_html:
            # Tự động cập nhật search_text từ content_html trong DB
            obj.search_text = extract_html_plain_text(obj.content_html)

        # 2. Nếu định dạng là MARKDOWN
        if obj.content_type == 'MARKDOWN':
            obj.search_text = extract_markdown_plain_text(obj.content_markdown)

        super().save_model(request, obj, form, change)

        # Đồng bộ quan hệ Many-to-Many ảnh đính kèm sau khi lưu
        if obj.content_type == 'MARKDOWN':
            sync_document_images(obj)
