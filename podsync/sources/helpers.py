from bs4 import BeautifulSoup


def html_content_by_attrs(
    html: BeautifulSoup, html_tag: str, attrs: dict[str, str]
) -> str | None:
    tag = html.find(html_tag, attrs=attrs)
    if tag is None:
        return None
    if isinstance(tag, str):
        return tag
    content = tag.get("content")
    if content is not None:
        return content[0] if isinstance(content, list) else content
    return tag.get_text()


def meta_content_by_attrs(html: BeautifulSoup, attrs: dict[str, str]) -> str | None:
    return html_content_by_attrs(html, "meta", attrs)
