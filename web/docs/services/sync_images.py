import re
from docs.models import ImageAttachment

def sync_document_images(document):
    """
    Quét content_markdown của document để tìm các link ảnh /media/(images/...)
    và đồng bộ quan hệ Many-to-Many giữa document và ImageAttachment.
    Một ảnh có thể liên kết với nhiều bài viết (hoặc chưa liên kết bài nào).
    """
    if not document.content_markdown:
        document.images.clear()
        return

    # Tìm các key ảnh: images/YYYY/MM/<uuid>.<ext>
    pattern = r'/media/(images/[a-zA-Z0-9_\-\./]+)'
    found_keys = set(re.findall(pattern, document.content_markdown))

    if found_keys:
        attachments = ImageAttachment.objects.filter(file__in=found_keys)
        document.images.set(attachments)
    else:
        document.images.clear()
