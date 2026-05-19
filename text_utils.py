import re
from collections import Counter
from typing import Dict, Iterable, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

try:
    import emoji as emoji_lib
except Exception:
    emoji_lib = None


def html_to_text(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text("\n", strip=True)


def shorten(text: str, limit: int = 800) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...【已截断】"


def extract_image_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html or "", "html.parser")
    links = []

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            links.append(urljoin(base_url, src))

    image_ext = re.compile(r"\.(png|jpg|jpeg|gif|webp|bmp|svg)(\?.*)?$", re.I)
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and image_ext.search(href):
            links.append(urljoin(base_url, href))

    result = []
    seen = set()
    for link in links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def extract_emojis(text: str) -> List[str]:
    text = text or ""
    if emoji_lib is not None:
        return [item["emoji"] for item in emoji_lib.emoji_list(text)]

    pattern = re.compile(
        "["
        "\U0001F1E6-\U0001F1FF"
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F7FF"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "☀-⛿"
        "✀-➿"
        "]+",
        flags=re.UNICODE,
    )
    return pattern.findall(text)


def count_emojis_from_texts(texts: Iterable[str]) -> Counter:
    counter = Counter()
    for text in texts:
        counter.update(extract_emojis(text))
    return counter