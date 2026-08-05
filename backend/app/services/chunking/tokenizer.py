"""
Token counting for chunk sizing.

tiktoken downloads its encoding file from the network the FIRST time a
given encoding is used, then caches it. That's a problem in an offline
or firewalled environment (e.g. this container before its first
internet-connected run) — so counting falls back to a whitespace-based
approximation rather than crashing the whole chunking job. The
approximation is deliberately conservative (overestimates slightly) so
chunks stay safely under CHUNK_MAX_TOKENS even when using it.
"""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_encoding = None
_tried_and_failed = False


def _get_encoding():
    global _encoding, _tried_and_failed
    if _encoding is not None or _tried_and_failed:
        return _encoding
    try:
        import tiktoken

        _encoding = tiktoken.get_encoding(settings.CHUNK_TOKENIZER_ENCODING)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"tiktoken_unavailable_using_fallback: {exc}")
        _tried_and_failed = True
    return _encoding


def count_tokens(text: str) -> int:
    encoding = _get_encoding()
    if encoding is not None:
        return len(encoding.encode(text))
    return _approximate_token_count(text)


def _approximate_token_count(text: str) -> int:
    """~1 token per 3.5 characters is a commonly-cited rough average for
    English text with this tokenizer family; used only when tiktoken's
    real encoding isn't available. Deliberately rounds up."""
    if not text:
        return 0
    return max(1, int(len(text) / 3.5) + 1)
