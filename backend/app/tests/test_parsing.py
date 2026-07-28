"""
Parsing tests focus on the pure logic (cleaning, chapter detection) and
the TXT path end-to-end, since those need no external binaries. PDF/EPUB/
DOCX extraction is exercised implicitly through the shared chapter
detector — the format-specific extractors are thin enough (a handful of
lines calling a well-known library) that the main risk is in the
cleaning/detection logic, which these tests cover directly.
"""

from app.services.parsing.chapter_detector import detect_chapters
from app.services.parsing.orchestrator import parse_book_content
from app.services.parsing.text_cleaner import clean_extracted_text, split_paragraphs


def test_clean_removes_standalone_page_numbers():
    raw = "Some text.\n\n42\n\nMore text."
    cleaned = clean_extracted_text(raw)
    assert "42" not in cleaned.split("\n")


def test_clean_rejoins_hyphenated_linebreaks():
    raw = "This is a trans-\nlation example."
    cleaned = clean_extracted_text(raw)
    assert "translation" in cleaned


def test_clean_collapses_multiple_blank_lines():
    raw = "Para one.\n\n\n\n\nPara two."
    cleaned = clean_extracted_text(raw)
    assert "\n\n\n" not in cleaned


def test_split_paragraphs_joins_wrapped_lines():
    text = "This is a\nwrapped paragraph.\n\nThis is another one."
    paragraphs = split_paragraphs(text)
    assert paragraphs == ["This is a wrapped paragraph.", "This is another one."]


def test_detect_chapters_finds_numbered_chapters():
    text = (
        "Chapter 1\nOnce upon a time.\n\n"
        "Chapter 2\nThe story continues.\n"
    )
    chapters = detect_chapters(text)
    assert len(chapters) == 2
    assert chapters[0].title == "Chapter 1"
    assert "Once upon a time" in chapters[0].text
    assert chapters[1].title == "Chapter 2"


def test_detect_chapters_falls_back_to_single_chapter():
    text = "Just a plain block of text with no headings at all."
    chapters = detect_chapters(text)
    assert len(chapters) == 1
    assert chapters[0].title == "Full Text"


def test_parse_book_content_txt_end_to_end():
    content = b"Chapter 1\nHello world.\n\nChapter 2\nGoodbye world.\n"
    chapters = parse_book_content("txt", content)
    assert len(chapters) == 2
    assert chapters[0].word_count > 0
    assert chapters[1].title == "Chapter 2"


def test_parse_book_content_unsupported_extension_raises():
    import pytest

    with pytest.raises(ValueError):
        parse_book_content("xyz", b"data")