import os
import boto3
from botocore.client import Config
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from docs.models import Department, Workflow, Document
from docs.services.extract_text import extract_markdown_plain_text, extract_html_plain_text

class Command(BaseCommand):
    help = 'Khởi tạo tài khoản Admin, SeaweedFS Storage và Dữ liệu mẫu quy trình BIM Lab (v3)'

    def handle(self, *args, **options):
        # 1. Khởi tạo Storage Bucket trên SeaweedFS
        self.stdout.write("=== [BIMLab Init] Khoi tao SeaweedFS Storage Bucket... ===")
        call_command('init_storage')

        # 2. Khởi tạo Admin User
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@bimlab.local')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')

        admin_user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password(password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f"Da tao Admin [{username}] thanh cong."))
        else:
            self.stdout.write(f"Admin [{username}] da ton tai.")

        # 3. Khởi tạo Bộ môn (Department)
        departments_data = [
            {'code': 'ARC', 'name': 'Kiến trúc (Architecture)'},
            {'code': 'STR', 'name': 'Kết cấu (Structure)'},
            {'code': 'MEP', 'name': 'Cơ điện (MEP Engineering)'},
            {'code': 'MNG', 'name': 'Quản lý & Điều phối BIM'},
            {'code': 'QC', 'name': 'Kiểm soát Chất lượng (Quality Control)'},
        ]
        dept_objs = {}
        for d in departments_data:
            obj, _ = Department.objects.get_or_create(code=d['code'], defaults={'name': d['name']})
            dept_objs[d['code']] = obj

        # 4. Khởi tạo Luồng công việc (Workflow)
        workflows_data = [
            {'name': 'Design', 'order': 1},
            {'name': 'Model', 'order': 2},
            {'name': 'Coordination', 'order': 3},
            {'name': 'Documentation', 'order': 4},
            {'name': 'Standards', 'order': 5},
        ]
        wf_objs = {}
        for w in workflows_data:
            obj, _ = Workflow.objects.get_or_create(name=w['name'], defaults={'order': w['order']})
            wf_objs[w['name']] = obj

        # 5. Khởi tạo File HTML mẫu lên SeaweedFS S3
        qc_html_content = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 24px; color: #1e293b; background: #ffffff; line-height: 1.5; font-size: 14px; }
h2 { color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; font-size: 18px; margin-top: 0; }
.badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; background: #ecfdf5; color: #047857; }
table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }
th, td { border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }
th { background: #f8fafc; font-weight: 600; color: #334155; }
tr:nth-child(even) td { background: #fafbfc; }
.notice { background: #f1f5f9; border-left: 4px solid #0284c7; padding: 12px; margin-top: 20px; font-size: 12px; color: #334155; }
</style>
</head>
<body>
<h2>Biên bản Kiểm tra Chất lượng Mô hình BIM Trước Phát hành (QC Checklist)</h2>
<p>Biên bản nghiệm thu kỹ thuật độc lập định dạng HTML chuẩn Single-file web page.</p>
<table>
<thead>
<tr>
<th>Hạng mục</th>
<th>Tiêu chí Đạt (Pass Criteria)</th>
<th>Trạng thái</th>
</tr>
</thead>
<tbody>
<tr>
<td>1. Shared Coordinates</td>
<td>Trùng khớp 100% gốc tọa độ CDE trung tâm dự án</td>
<td><span class="badge">ĐẠT (PASS)</span></td>
</tr>
<tr>
<td>2. Cảnh báo Revit Warnings</td>
<td>Không vượt quá 50 warnings cho mô hình chính</td>
<td><span class="badge">ĐẠT (PASS)</span></td>
</tr>
<tr>
<td>3. Phân vùng Worksets</td>
<td>Gán đúng workset theo từng chuyên ngành</td>
<td><span class="badge">ĐẠT (PASS)</span></td>
</tr>
</tbody>
</table>
<div class="notice">
<strong>Ghi chú:</strong> Tệp HTML độc lập này được bảo vệ trong sandbox iframe an toàn, ngăn chặn tấn công XSS chéo nguồn.
</div>
</body>
</html>"""

        qc_html_key = "html/qc_checklist_04.html"
        try:
            s3 = boto3.client(
                's3',
                endpoint_url=os.environ.get('SEAWEEDFS_S3_ENDPOINT', 'http://seaweedfs:8333'),
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'bimlab_s3_key_2026'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'bimlab_s3_secret_2026'),
                config=Config(signature_version='s3v4')
            )
            s3.put_object(
                Bucket=os.environ.get('AWS_STORAGE_BUCKET_NAME', 'bimlab-media'),
                Key=qc_html_key,
                Body=qc_html_content.encode('utf-8'),
                ContentType='text/html; charset=utf-8'
            )
            self.stdout.write(self.style.SUCCESS(f"Da tai file HTML mau [{qc_html_key}] len SeaweedFS."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Khong the tai file HTML mau len S3: {e}"))

        # 6. Khởi tạo các Document mẫu (PUBLISHED)
        sample_docs = [
            {
                'code': 'ARC-Model-01',
                'title': 'Quy trình Thiết lập Tọa độ & Dựng hình Mô hình Kiến trúc LOD 350',
                'department': dept_objs['ARC'],
                'workflow': wf_objs['Model'],
                'content_type': 'MARKDOWN',
                'status': 'PUBLISHED',
                'markdown': """## 1. Mục tiêu và Phạm vi Áp dụng

Quy trình này quy định các bước thực hiện mô hình hóa đối tượng Kiến trúc trong môi trường **Autodesk Revit** đạt mức độ phát triển **LOD 350** theo tiêu chuẩn BIM Forum.

> [!NOTE]
> Mọi dự án phải tuân thủ việc liên kết file Tọa độ chung (*Shared Coordinates*) từ file Master Coordinates do Trưởng nhóm BIM ban hành trước khi bắt đầu dựng hình.

---

## 2. Lưu đồ Quy trình Thực hiện

```mermaid
flowchart TD
    A([Nhận File Master Coordinates]) --> B[Link CAD/RVT & Acquire Coordinates]
    B --> C[Thiết lập Lưới trục Grids & Cao độ Levels]
    C --> D[Dựng Cấu kiện Vỏ bao tường/kính]
    D --> E{Kiểm tra Dung sai Hình học}
    E -->|Sai số > 3mm| D
    E -->|Đạt tiêu chuẩn| F[Dựng Chi tiết Hoàn thiện & Cửa LOD 350]
    F --> G([Nghiệm thu Nội bộ Bộ môn])
```

---

## 3. Bảng Tiêu chuẩn Cấu kiện LOD 350

| Nhóm Đối tượng | Danh mục Revit | Yêu cầu Hình học (Geometry) | Yêu cầu Tham số (Data) |
|---|---|---|---|
| **Vách tường** | *Walls* | Dựng tách lớp hoàn thiện (*Finishes*) và tường thô xây trát | `FireRating`, `OmniClass`, `AcousticRating` |
| **Cửa đi/Cửa sổ** | *Doors / Windows* | Thể hiện khung bao, nẹp chỉ, hướng mở 2D/3D | `Mark`, `HardwareSet`, `Manufacturer` |
| **Sàn kiến trúc** | *Floors* | Thể hiện lớp dốc cán nền, len chân tường | `FinishMaterial`, `SlipResistance` |

---

## 4. Các Lưu ý Kỹ thuật Bắt buộc

> [!WARNING]
> Tuyệt đối không sử dụng công cụ *In-Place Massing* để tạo cấu kiện kiến trúc cố định. Tất cả đối tượng lặp lại bắt buộc phải tạo bằng **Loadable Family**.

> [!TIP]
> Sử dụng công cụ **Worksharing Monitor** để kiểm tra đồng bộ, giải phóng quyền chỉnh sửa (*Relinquish Borrowed Elements*) trước 17h30 hàng ngày nhằm tránh xung đột file trung tâm (*Central File*).
"""
            },
            {
                'code': 'STR-Coord-02',
                'title': 'Quy trình Phối hợp & Xử lý Xung đột Kết cấu - Cơ điện (Clash Detection)',
                'department': dept_objs['STR'],
                'workflow': wf_objs['Coordination'],
                'content_type': 'MARKDOWN',
                'status': 'PUBLISHED',
                'markdown': """## 1. Nguyên tắc Xử lý Xung đột

Giai đoạn điều phối đa bộ môn yêu cầu tối ưu hóa không gian chịu lực của công trình, đồng thời đảm bảo không gian kỹ thuật cho các tuyến ống MEP trọng yếu.

> [!IMPORTANT]
> Dầm chuyển (*Transfer Beam*) và Cột vách chịu lực là các cấu kiện bất khả xâm phạm. Tuyệt đối không đục lỗ xuyên dầm (*Opening*) tại vùng ứng suất cắt cao nếu chưa có phê duyệt từ Chủ trì Kết cấu.

---

## 2. Ma trận Phân loại Mức độ Xung đột (Clash Matrix)

| Cặp Bộ môn So sánh | Dung sai Cho phép (*Tolerance*) | Mức độ Ưu tiên (*Priority*) | Hướng xử lý |
|---|---|---|---|
| **Cột/Vách vs Tuyến ống chính** | `0 mm` | **Cấp độ 1 (Critical)** | Dịch chuyển tuyến ống MEP |
| **Dầm BTCT vs Ống gió HVAC** | `25 mm` | **Cấp độ 2 (High)** | Xem xét mở Sleeves/Opening theo tiêu chuẩn |
| **Sàn BTCT vs Ống thoát nước** | `10 mm` | **Cấp độ 3 (Medium)** | Bố trí lỗ mở xuyên sàn kỹ thuật |
"""
            },
            {
                'code': 'MEP-Std-03',
                'title': 'Tiêu chuẩn Đặt tên Hệ thống & Mã màu Nhận diện Đường ống MEP',
                'department': dept_objs['MEP'],
                'workflow': wf_objs['Standards'],
                'content_type': 'MARKDOWN',
                'status': 'PUBLISHED',
                'markdown': """## 1. Quy ước Tiền tố Hệ thống (System Abbreviation)

Nhằm đảm bảo tính nhất quán dữ liệu xuyên suốt mô hình và hồ sơ bóc tách khối lượng (QTO):

- **Hệ Thống Cấp Nước Lạnh:** `CW` (*Cold Water Supply*)
- **Hệ Thống Cấp Nước Nóng:** `HW` (*Hot Water Supply*)
- **Hệ Thống Thoát Nước Thải:** `WW` (*Waste Water / Soil Water*)
- **Hệ Thống Cấp Khí Tươi HVAC:** `SA` (*Supply Air Duct*)
- **Hệ Thống Chữa Cháy Spinkler:** `FP` (*Fire Protection Sprinkler*)

> [!TIP]
> Tất cả các View Template cho hệ thống MEP phải gắn Filter kèm màu sắc này. Không ghi đè trực tiếp (*Override Graphics*) bằng tay lên từng cấu kiện đơn lẻ.
"""
            },
            {
                'code': 'QC-Check-04',
                'title': 'Check-list Nghiệm thu Mô hình BIM Trước khi Phát hành Hồ sơ Bản vẽ (File HTML Độc lập)',
                'department': dept_objs['QC'],
                'workflow': wf_objs['Standards'],
                'content_type': 'HTML',
                'status': 'PUBLISHED',
                'content_html': qc_html_content,
                'html_file': qc_html_key,
                'search_text': extract_html_plain_text(qc_html_content),
            }
        ]

        now = timezone.now()
        for d in sample_docs:
            doc, created = Document.objects.get_or_create(
                code=d['code'],
                defaults={
                    'title': d['title'],
                    'department': d['department'],
                    'workflow': d['workflow'],
                    'content_type': d['content_type'],
                    'status': d['status'],
                    'content_markdown': d.get('markdown', ''),
                    'content_html': d.get('content_html', ''),
                    'html_file': d.get('html_file', ''),
                    'search_text': d.get('search_text', '') or extract_markdown_plain_text(d.get('markdown', '')),
                    'author': admin_user,
                    'published_at': now,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Da tao quy trinh mau [{doc.code}] {doc.title}"))
            else:
                if d.get('content_html') and not doc.content_html:
                    doc.content_html = d['content_html']
                    doc.save()
                    self.stdout.write(f"Da cap nhat content_html cho [{doc.code}].")
                else:
                    self.stdout.write(f"Quy trinh [{doc.code}] da ton tai.")

        self.stdout.write(self.style.SUCCESS("=== Hoan tat khoi tao du lieu Plan v3! ==="))
