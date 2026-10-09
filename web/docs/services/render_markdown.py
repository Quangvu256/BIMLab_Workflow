import re
import markdown
from bs4 import BeautifulSoup
import nh3

def process_github_alerts(html_content: str) -> str:
    """
    Chuyển đổi cú pháp Alert của GitHub (> [!NOTE], > [!WARNING], ...)
    thành các khối Callout tinh tế, tối giản, không gây chói mắt.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    blockquotes = soup.find_all('blockquote')

    alert_configs = {
        'NOTE': {
            'label': 'Lưu ý',
            'color_class': 'border-slate-400 bg-slate-50 text-slate-800',
            'title_color': 'text-slate-700 font-semibold',
            'icon': '<svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>'
        },
        'TIP': {
            'label': 'Mẹo',
            'color_class': 'border-emerald-500 bg-emerald-50/50 text-slate-800',
            'title_color': 'text-emerald-800 font-semibold',
            'icon': '<svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14H8a4 4 0 01-.824-7.915A4.004 4.004 0 0112 14z"></path></svg>'
        },
        'IMPORTANT': {
            'label': 'Quan trọng',
            'color_class': 'border-slate-700 bg-slate-100 text-slate-900',
            'title_color': 'text-slate-900 font-bold',
            'icon': '<svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>'
        },
        'WARNING': {
            'label': 'Cảnh báo',
            'color_class': 'border-amber-400 bg-amber-50/50 text-slate-800',
            'title_color': 'text-amber-800 font-semibold',
            'icon': '<svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>'
        },
        'CAUTION': {
            'label': 'Lưu ý rủi ro',
            'color_class': 'border-rose-400 bg-rose-50/50 text-slate-800',
            'title_color': 'text-rose-800 font-semibold',
            'icon': '<svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>'
        }
    }

    for bq in blockquotes:
        first_p = bq.find('p')
        if not first_p:
            continue
        text = first_p.decode_contents().strip()
        match = re.match(r'^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](?:\s*<br\s*\/?>|\s+)?(.*)', text, re.DOTALL | re.IGNORECASE)
        if match:
            alert_type = match.group(1).upper()
            remaining_content = match.group(2).strip()
            cfg = alert_configs.get(alert_type)
            if cfg:
                if remaining_content:
                    first_p.clear()
                    first_p.append(BeautifulSoup(remaining_content, 'html.parser'))
                else:
                    first_p.decompose()

                callout_div = soup.new_tag('div')
                callout_div['class'] = f"callout-box my-3 p-3 rounded border-l-4 {cfg['color_class']}"

                header_div = soup.new_tag('div')
                header_div['class'] = f"flex items-center gap-1.5 mb-1 text-xs {cfg['title_color']}"
                header_div.append(BeautifulSoup(cfg['icon'], 'html.parser'))

                title_span = soup.new_tag('span')
                title_span.string = cfg['label']
                header_div.append(title_span)
                callout_div.append(header_div)

                body_div = soup.new_tag('div')
                body_div['class'] = "text-xs leading-relaxed space-y-1 text-slate-700"
                for child in list(bq.children):
                    body_div.append(child)
                callout_div.append(body_div)

                bq.replace_with(callout_div)

    # Mermaid diagram detection
    for pre in soup.find_all('pre'):
        code = pre.find('code')
        if code and ('language-mermaid' in code.get('class', []) or 'mermaid' in code.get('class', [])):
            mermaid_div = soup.new_tag('div')
            mermaid_div['class'] = "mermaid my-4 p-3 bg-white border border-slate-200 rounded flex justify-center overflow-x-auto text-xs"
            mermaid_div.string = code.get_text()
            pre.replace_with(mermaid_div)

    return str(soup)


def sanitize_html(html_content: str) -> str:
    """Khử nhiễm HTML an toàn bằng nh3 (cho phép các thẻ cần thiết của Markdown)"""
    allowed_tags = {
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'b', 'strong', 'i', 'em', 'u', 's', 'del',
        'a', 'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'div', 'span', 'img', 'hr', 'br', 'svg', 'path'
    }
    allowed_attrs = {
        '*': {'class', 'id'},
        'a': {'href', 'title', 'target', 'rel'},
        'img': {'src', 'alt', 'title', 'loading'},
        'svg': {'class', 'fill', 'viewbox', 'width', 'height'},
        'path': {'d', 'fill-rule', 'clip-rule', 'fill'}
    }
    try:
        return nh3.clean(html_content, tags=allowed_tags, attributes=allowed_attrs)
    except Exception:
        return html_content


def render_markdown(markdown_text: str) -> dict:
    """Biên dịch Markdown sang HTML với TOC Extension, Alert Callouts và Sanitize nh3"""
    md = markdown.Markdown(
        extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.toc',
            'markdown.extensions.attr_list',
            'markdown.extensions.nl2br',
            'markdown.extensions.sane_lists',
        ],
        extension_configs={
            'markdown.extensions.toc': {
                'permalink': True,
                'toc_depth': '2-4',
                'title': 'Mục lục',
            }
        }
    )

    raw_html = md.convert(markdown_text or '')
    with_alerts = process_github_alerts(raw_html)
    safe_html = sanitize_html(with_alerts)

    return {
        'html': safe_html,
        'toc_html': md.toc,
        'toc_tokens': getattr(md, 'toc_tokens', []),
    }
