from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.client import Config
from docs.models import ImageAttachment

class Command(BaseCommand):
    help = 'Dọn dẹp ảnh mồ côi (không thuộc bài viết nào và cũ hơn 7 ngày) trên SeaweedFS và DB'

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(days=7)
        orphans = ImageAttachment.objects.filter(
            documents__isnull=True,
            uploaded_at__lt=threshold
        )

        count = orphans.count()
        if count == 0:
            self.stdout.write("Khong co anh mo coi nao can don dep.")
            return

        s3 = boto3.client(
            's3',
            endpoint_url=settings.SEAWEEDFS_S3_ENDPOINT,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4')
        )

        deleted = 0
        for orphan in orphans:
            try:
                s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=orphan.file)
                orphan.delete()
                deleted += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Loi xoa file {orphan.file}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Da don dep thanh cong {deleted}/{count} anh mo coi."))
