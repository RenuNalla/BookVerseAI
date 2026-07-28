"""
DOCX text extraction. python-docx exposes each paragraph with its style
name, which lets us detect chapter headings (Word's "Heading 1" style)
far more reliably than regex guessing on plain text — so DOCX chapter
detection is more accurate than PDF/TXT.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO


@dataclass
class DocxParagraph:
    text: str
    is_heading: bool


def extract_docx_paragraphs(content: bytes) -> list[DocxParagraph]:
    from docx import Document

    doc = Document(BytesIO(content))
    result: list[DocxParagraph] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        is_heading = para.style.name.lower().startswith("heading") if para.style else False
        result.append(DocxParagraph(text=text, is_heading=is_heading))

    return result