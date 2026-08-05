"""
Intelligent chunking: splits a chapter's cleaned text into chunks that
(a) fit under CHUNK_MAX_TOKENS and (b) never split a sentence in half,
since a translation model given half a sentence produces worse output
than one given a slightly-short-of-max chunk.

Strategy, in order of preference:
  1. Pack whole paragraphs together until the next one would overflow.
  2. A paragraph too big on its own gets split into sentences and those
     are packed the same way.
  3. A single sentence still too big (rare — a huge run-on, or a
     mis-detected paragraph boundary) gets hard-split by token count as
     a last resort, since SOME chunk has to be produced either way.

Context preservation: each chunk carries a short `context_snippet` — the
tail of the previous chunk's text — not for translation itself, but so
Phase 6 can give the translation prompt a hint of what came immediately
before, improving pronoun/tense consistency across chunk boundaries
without re-sending the whole previous chunk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import settings
from app.services.chunking.tokenizer import count_tokens
from app.services.parsing.text_cleaner import split_paragraphs

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\u2018\u201c])")
CONTEXT_SNIPPET_CHARS = 200


@dataclass
class Chunk:
    content: str
    token_count: int
    char_count: int
    context_snippet: str | None


def chunk_chapter(chapter_content: str, max_tokens: int | None = None) -> list[Chunk]:
    max_tokens = max_tokens or settings.CHUNK_MAX_TOKENS
    paragraphs = split_paragraphs(chapter_content)
    if not paragraphs:
        return []

    units = _units_within_budget(paragraphs, max_tokens)
    return _pack_units(units, max_tokens)


def _units_within_budget(paragraphs: list[str], max_tokens: int) -> list[str]:
    """Breaks any paragraph that alone exceeds max_tokens down into
    sentences (and, as a last resort, hard token slices), so every unit
    handed to the packer is guaranteed chunk-able on its own."""
    units: list[str] = []
    for para in paragraphs:
        if count_tokens(para) <= max_tokens:
            units.append(para)
            continue

        sentences = _SENTENCE_SPLIT.split(para)
        for sentence in sentences:
            if count_tokens(sentence) <= max_tokens:
                units.append(sentence)
            else:
                units.extend(_hard_split(sentence, max_tokens))
    return units


def _hard_split(text: str, max_tokens: int) -> list[str]:
    """Last-resort split by character count, calibrated against the
    approximate chars-per-token ratio. Only reached for pathological
    input (e.g. one sentence with no punctuation for thousands of words)."""
    approx_chars_per_chunk = max(200, max_tokens * 3)
    return [text[i : i + approx_chars_per_chunk] for i in range(0, len(text), approx_chars_per_chunk)]


def _pack_units(units: list[str], max_tokens: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    current_parts: list[str] = []
    current_tokens = 0

    def flush():
        nonlocal current_parts, current_tokens
        if not current_parts:
            return
        content = "\n\n".join(current_parts)
        previous_tail = chunks[-1].content[-CONTEXT_SNIPPET_CHARS:] if chunks else None
        chunks.append(
            Chunk(
                content=content,
                token_count=current_tokens,
                char_count=len(content),
                context_snippet=previous_tail,
            )
        )
        current_parts = []
        current_tokens = 0

    for unit in units:
        unit_tokens = count_tokens(unit)
        if current_parts and current_tokens + unit_tokens > max_tokens:
            flush()
        current_parts.append(unit)
        current_tokens += unit_tokens

    flush()
    return chunks
