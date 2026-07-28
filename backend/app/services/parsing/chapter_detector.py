"""
Chapter detection for formats that don't already give us chapter
boundaries (PDF, TXT — DOCX uses heading styles, EPUB uses spine items,
see their respective extractors). Works on cleaned, page-joined text.

Heuristic, not a parser: looks for a line that is SHORT (headings are
short) and matches a common chapter-heading pattern. A book with none
of these patterns falls back to one single chapter containing the
whole text, which is still useful — Phase 5's chunker doesn't need
chapter boundaries to be perfect.
"""

import re
from dataclasses import dataclass

_MAX_HEADING_LINE_LENGTH = 80

_CHAPTER_PATTERNS = [
    re.compile(r"^\s*chapter\s+([0-9ivxlcdm]+)\b[\s:.\-–—]*(.*)$", re.IGNORECASE),
    re.compile(r"^\s*part\s+([0-9ivxlcdm]+)\b[\s:.\-–—]*(.*)$", re.IGNORECASE),
    re.compile(r"^\s*(\d{1,3})[.\-–—]\s+(.+)$"),  # "1. The Beginning"
]


@dataclass
class DetectedChapter:
    title: str
    text: str


def detect_chapters(full_text: str) -> list[DetectedChapter]:
    lines = full_text.split("\n")

    # (line_index, matched_title) for every line that looks like a heading
    heading_positions: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > _MAX_HEADING_LINE_LENGTH:
            continue
        for pattern in _CHAPTER_PATTERNS:
            match = pattern.match(stripped)
            if match:
                title = stripped if not match.group(0).strip() == stripped else stripped
                heading_positions.append((i, stripped))
                break

    if not heading_positions:
        return [DetectedChapter(title="Full Text", text=full_text.strip())]

    chapters: list[DetectedChapter] = []
    for idx, (line_no, title) in enumerate(heading_positions):
        start = line_no + 1
        end = heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        body = "\n".join(lines[start:end]).strip()
        if body:  # skip a "chapter heading" with no following content (false positive)
            chapters.append(DetectedChapter(title=title, text=body))

    # Every heading turned out to be a false positive (e.g. no body text
    # followed any of them) — safer to fall back than return nothing.
    return chapters or [DetectedChapter(title="Full Text", text=full_text.strip())]