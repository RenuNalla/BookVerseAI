"""
Text cleaning. Runs on raw extracted text from any source format before
chapter detection and paragraph splitting see it. Kept as small, named,
independently-testable functions rather than one big regex blob, since
each one addresses a distinct, common artifact of text extraction.
"""

import re

_MULTI_BLANK_LINES = re.compile(r"\n{3,}")
_TRAILING_SPACES = re.compile(r"[ \t]+\n")
_HYPHEN_LINEBREAK = re.compile(r"(\w)-\n(\w)")
# A line that's just a number (with optional surrounding whitespace/dashes)
# on its own is almost always a page number artifact from PDF extraction.
_STANDALONE_PAGE_NUMBER = re.compile(r"^\s*[-–—]?\s*\d{1,4}\s*[-–—]?\s*$")


def clean_extracted_text(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Rejoin words split across a line break by hyphenation, e.g.
    # "trans-\nlation" -> "translation". Common in PDF text layers.
    text = _HYPHEN_LINEBREAK.sub(r"\1\2", text)

    lines = [line for line in text.split("\n") if not _STANDALONE_PAGE_NUMBER.match(line)]
    text = "\n".join(lines)

    text = _TRAILING_SPACES.sub("\n", text)
    text = _MULTI_BLANK_LINES.sub("\n\n", text)

    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    """Splits cleaned chapter text into paragraphs on blank lines.
    Single line breaks within a paragraph (common in PDF extraction,
    where every wrapped line is its own '\\n') are treated as spaces."""
    raw_paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = []
    for para in raw_paragraphs:
        collapsed = " ".join(line.strip() for line in para.split("\n") if line.strip())
        if collapsed:
            paragraphs.append(collapsed)
    return paragraphs