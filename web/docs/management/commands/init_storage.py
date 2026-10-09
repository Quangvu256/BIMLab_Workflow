import os
import boto3
from botocore.client import Config
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Khởi tạo S3 Bucket bimlab-media trên SeaweedFS (idempotent)'

    def handle(self, *args, **options):
        s3_endpoint = getattr(settings, 'SEAWEEDFS_S3_ENDPOINT', 'http://seaweedfs:8333')
        access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', 'bimlab_s3_key_2026')
        secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', 'bimlab_s3_secret_2026')
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'bimlab-media')

        try:
            s3 = boto3.client(
                's3',
                endpoint_url=s3_endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=Config(signature_version='s3v4')
            )

            # Kiểm tra xem Bucket đã tồn tại chưa
            try:
                s3.head_bucket(Bucket=bucket_name)
                self.stdout.write(f"SeaweedFS Bucket [{bucket_name}] da ton tai.")
            except Exception:
                s3.create_bucket(Bucket=bucket_name)
                self.stdout.write(self.style.SUCCESS(f"Da tao moi SeaweedFS Bucket [{bucket_name}]."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Loi ket noi SeaweedFS: {e}"))
