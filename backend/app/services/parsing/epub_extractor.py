"""
EPUB text extraction. EPUBs are already split into "spine" items —
almost always one per chapter — so unlike PDF/TXT we get chapter
boundaries for free from the file format itself instead of having to
guess them with regex. Each item's HTML is stripped down to plain text.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO


@dataclass
class EpubSection:
    title: str | None
    text: str


def extract_epub_sections(content: bytes) -> list[EpubSection]:
    import ebooklib
    from bs4 import BeautifulSoup
    from ebooklib import epub

    book = epub.read_epub(BytesIO(content), options={"ignore_ncx": True})
    sections: list[EpubSection] = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")

        # Prefer an explicit heading tag as the chapter title; fall back
        # to None and let the chapter_detector assign a generic title.
        heading_tag = soup.find(["h1", "h2", "h3"])
        title = heading_tag.get_text(strip=True) if heading_tag else None

        text = soup.get_text(separator="\n").strip()
        if text:
            sections.append(EpubSection(title=title, text=text))

    return sections