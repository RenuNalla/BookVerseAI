"""
Format-agnostic entrypoint: given raw file bytes + extension, returns a
list of (title, cleaned_text) chapters. This is the ONLY function the
Celery task calls — it doesn't know or care whether the book was a PDF,
EPUB, DOCX, or TXT. Each format branch below is responsible for getting
its own extractor's output into that same shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.parsing.chapter_detector import detect_chapters
from app.services.parsing.docx_extractor import extract_docx_paragraphs
from app.services.parsing.epub_extractor import extract_epub_sections
from app.services.parsing.pdf_extractor import extract_pdf_pages
from app.services.parsing.text_cleaner import clean_extracted_text


@dataclass
class ParsedChapter:
    title: str
    content: str
    word_count: int


def parse_book_content(extension: str, content: bytes) -> list[ParsedChapter]:
    if extension == "pdf":
        chapters = _parse_pdf(content)
    elif extension == "docx":
        chapters = _parse_docx(content)
    elif extension == "epub":
        chapters = _parse_epub(content)
    elif extension == "txt":
        chapters = _parse_txt(content)
    else:
        raise ValueError(f"No parser registered for extension: {extension}")

    return [
        ParsedChapter(title=title, content=text, word_count=len(text.split()))
        for title, text in chapters
        if text.strip()
    ]


def _parse_pdf(content: bytes) -> list[tuple[str, str]]:
    pages = extract_pdf_pages(content)
    full_text = clean_extracted_text("\n\n".join(pages))
    return [(c.title, c.text) for c in detect_chapters(full_text)]


def _parse_txt(content: bytes) -> list[tuple[str, str]]:
    raw = content.decode("utf-8", errors="replace")
    full_text = clean_extracted_text(raw)
    return [(c.title, c.text) for c in detect_chapters(full_text)]


def _parse_docx(content: bytes) -> list[tuple[str, str]]:
    paragraphs = extract_docx_paragraphs(content)
    if not paragraphs:
        return []

    # Word's "Heading 1/2/3" style is a reliable chapter marker — use it
    # directly instead of falling back to regex guessing on plain text.
    if not any(p.is_heading for p in paragraphs):
        full_text = clean_extracted_text("\n\n".join(p.text for p in paragraphs))
        return [(c.title, c.text) for c in detect_chapters(full_text)]

    chapters: list[tuple[str, str]] = []
    current_title = "Introduction"
    current_body: list[str] = []
    for para in paragraphs:
        if para.is_heading:
            if current_body:
                chapters.append((current_title, clean_extracted_text("\n\n".join(current_body))))
            current_title = para.text
            current_body = []
        else:
            current_body.append(para.text)
    if current_body:
        chapters.append((current_title, clean_extracted_text("\n\n".join(current_body))))

    return chapters


def _parse_epub(content: bytes) -> list[tuple[str, str]]:
    sections = extract_epub_sections(content)
    result = []
    for i, section in enumerate(sections, start=1):
        title = section.title or f"Section {i}"
        result.append((title, clean_extracted_text(section.text)))
    return result