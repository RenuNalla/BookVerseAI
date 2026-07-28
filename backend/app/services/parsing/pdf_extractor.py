"""
PDF text extraction.

Most PDFs have a real text layer and pypdf reads it directly — fast,
no dependencies beyond pypdf. Scanned books (photographed or
image-only PDFs) have NO text layer at all, so page.extract_text()
comes back empty; for those pages we fall back to OCR via pytesseract.

OCR is deliberately per-page and lazy: we only pay the OCR cost for
pages that actually need it, not the whole book, since OCR is roughly
1-2 orders of magnitude slower than reading an existing text layer.
"""

from __future__ import annotations

from io import BytesIO

from app.core.logging import get_logger

logger = get_logger(__name__)

# A page is considered "image-only" (needs OCR) if pypdf extracts fewer
# than this many characters from it — a real text page has hundreds.
MIN_CHARS_FOR_TEXT_LAYER = 20


def extract_pdf_pages(content: bytes) -> list[str]:
    """Returns one string per page, using OCR only where the page has
    no usable text layer. Never raises — a page that fails every
    extraction method comes back as an empty string rather than
    aborting the whole book."""
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    pages: list[str] = []
    ocr_page_indices: list[int] = []

    for i, page in enumerate(reader.pages):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"pdf_page_extract_failed: page={i} - {exc}")
            text = ""

        if len(text) < MIN_CHARS_FOR_TEXT_LAYER:
            ocr_page_indices.append(i)
            pages.append("")  # placeholder, filled in below if OCR succeeds
        else:
            pages.append(text)

    if ocr_page_indices:
        logger.info(f"pdf_ocr_fallback: {len(ocr_page_indices)} of {len(pages)} pages")
        ocr_results = _ocr_pages(content, ocr_page_indices)
        for idx, ocr_text in ocr_results.items():
            pages[idx] = ocr_text

    return pages


def _ocr_pages(content: bytes, page_indices: list[int]) -> dict[int, str]:
    """Best-effort OCR. If tesseract/poppler aren't installed in this
    environment, logs a warning and returns empty strings for those
    pages rather than failing the whole parse job — a book with a few
    unreadable scanned pages is still more useful than no book at all."""
    results: dict[int, str] = {}
    try:
        import pytesseract
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(content, dpi=200)
        for idx in page_indices:
            if idx >= len(images):
                continue
            try:
                results[idx] = pytesseract.image_to_string(images[idx]).strip()
            except Exception as exc:  # noqa: BLE001
                logger.error(f"ocr_page_failed: page={idx} - {exc}")
                results[idx] = ""
    except Exception as exc:  # noqa: BLE001
        logger.error(f"ocr_unavailable: {exc}")
        for idx in page_indices:
            results[idx] = ""

    return results