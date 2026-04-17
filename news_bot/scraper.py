import requests
from bs4 import BeautifulSoup
from typing import Optional

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_article_data(url: str) -> dict:
    try:
        response = requests.get(url, headers=_HEADERS, timeout=10, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        return {
            "image_url": _extract_image(soup),
            "body": _extract_body(soup),
        }
    except Exception:
        return {"image_url": None, "body": None}


def _extract_image(soup: BeautifulSoup) -> Optional[str]:
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"].strip()

    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        return tw["content"].strip()

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("http"):
            continue
        width = img.get("width")
        if width:
            try:
                if int(str(width).replace("px", "")) > 300:
                    return src
            except (ValueError, TypeError):
                pass

    return None


def _extract_body(soup: BeautifulSoup) -> Optional[str]:
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    best_element = None
    max_p_count = 0

    for element in soup.find_all(["article", "main", "section", "div"]):
        p_count = len(element.find_all("p"))
        if p_count > max_p_count:
            max_p_count = p_count
            best_element = element

    if best_element is None or max_p_count < 2:
        best_element = soup.body if soup.body else soup

    paragraphs = best_element.find_all("p")
    text_parts = [
        p.get_text(separator=" ", strip=True)
        for p in paragraphs
        if len(p.get_text(strip=True)) > 30
    ]

    if not text_parts:
        return None

    body = "\n".join(text_parts).strip()

    if len(body) < 100:
        return None

    return body
