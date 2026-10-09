from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse

class Department(models.Model):
    """Bộ môn chuyên ngành: ARC (Kiến trúc), STR (Kết cấu), MEP (Cơ điện)..."""
    code = models.CharField(max_length=20, unique=True, verbose_name="Mã bộ môn (ARC, STR, MEP...)")
    name = models.CharField(max_length=100, verbose_name="Tên bộ môn")
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['code']
        verbose_name = "Bộ môn"
        verbose_name_plural = "Danh mục Bộ môn"

    def __str__(self):
        return f"[{self.code}] {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code)
        super().save(*args, **kwargs)


class Workflow(models.Model):
    """Phân loại luồng công việc: Design, Modeling, Coordination, Documentation, Standards..."""
    name = models.CharField(max_length=100, verbose_name="Tên luồng công việc")
    slug = models.SlugField(max_length=100, unique=True)
    order = models.IntegerField(default=0, verbose_name="Thứ tự hiển thị")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Luồng công việc"
        verbose_name_plural = "Danh mục Luồng công việc"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PublishedManager(models.Manager):
    """Manager lọc chỉ lấy bài PUBLISHED cho người xem công cộng"""
    def get_queryset(self):
        return super().get_queryset().filter(status='PUBLISHED')


class ImageAttachment(models.Model):
    """Hình ảnh tải lên lưu trữ trên SeaweedFS S3"""
    file = models.CharField(max_length=255, unique=True, db_index=True, verbose_name="Key file trên S3 (images/YYYY/MM/<uuid>.<ext>)")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Người tải lên")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm tải lên")

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Hình ảnh đính kèm"
        verbose_name_plural = "Thư viện Hình ảnh S3"

    def __str__(self):
        return self.file

    @property
    def url(self):
        return f"/media/{self.file}"


class Document(models.Model):
    """Tài liệu Quy trình & Hướng dẫn kỹ thuật BIM"""

    CONTENT_TYPE_CHOICES = [
        ('MARKDOWN', 'Markdown'),
        ('HTML', 'HTML Độc lập (1 file)'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Bản thảo (Draft)'),
        ('PUBLISHED', 'Đã xuất bản (Published)'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Mã quy trình",
        help_text="Ví dụ: ARC-Model-01, STR-Coord-02"
    )
    title = models.CharField(max_length=255, verbose_name="Tiêu đề quy trình")
    slug = models.SlugField(max_length=255, unique=True)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='MARKDOWN',
        verbose_name="Định dạng nội dung"
    )

    # 1. Định dạng Markdown
    content_markdown = models.TextField(blank=True, default='', verbose_name="Nội dung Markdown")

    # 2. Định dạng HTML (Lưu trực tiếp nội dung file HTML vào PostgreSQL DB)
    content_html = models.TextField(blank=True, default='', verbose_name="Nội dung HTML (lưu trực tiếp trong CSDL)")

    # Key file HTML dự phòng (nếu có)
    html_file = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Đường dẫn file HTML (tùy chọn)"
    )

    search_text = models.TextField(blank=True, default='', verbose_name="Text thuần tìm kiếm (tự sinh)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Trạng thái")

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='documents', verbose_name="Bộ môn")
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='documents', verbose_name="Luồng công việc")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents', verbose_name="Tác giả")

    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời điểm xuất bản")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật gần nhất")

    # Quan hệ Many-to-Many ảnh đính kèm (sync tự động khi lưu)
    images = models.ManyToManyField(ImageAttachment, related_name='documents', blank=True, verbose_name="Hình ảnh liên kết")

    # Managers
    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ['department', 'code']
        verbose_name = "Tài liệu Quy trình"
        verbose_name_plural = "Danh mục Tài liệu Quy trình"

    def __str__(self):
        return f"[{self.code}] {self.title}"

    def get_absolute_url(self):
        return reverse('doc_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.code}-{self.title}")
        super().save(*args, **kwargs)
