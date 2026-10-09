import re
from bs4 import BeautifulSoup

def extract_markdown_plain_text(markdown_text: str) -> str:
    """Loại bỏ ký tự cú pháp Markdown để trích xuất văn bản thuần cho tìm kiếm"""
    if not markdown_text:
        return ""
    
    # Loại bỏ code block
    text = re.sub(r'```.*?```', ' ', markdown_text, flags=re.DOTALL)
    # Loại bỏ inline code
    text = re.sub(r'`.*?`', ' ', text)
    # Loại bỏ link và ảnh: ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    # Loại bỏ tiêu đề #
    text = re.sub(r'#+\s*', ' ', text)
    # Loại bỏ in đậm, in nghiêng
    text = re.sub(r'[*_~]', ' ', text)
    # Loại bỏ alert syntax
    text = re.sub(r'>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]', ' ', text, flags=re.IGNORECASE)
    # Loại bỏ dấu trích dẫn >
    text = re.sub(r'>\s*', ' ', text)
    # Gom khoảng trắng
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_html_plain_text(html_text: str) -> str:
    """Trích xuất văn bản thuần từ tài liệu HTML"""
    if not html_text:
        return ""
    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        # Loại bỏ script, style
        for s in soup(['script', 'style']):
            s.decompose()
        text = soup.get_text(separator=' ')
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ""
