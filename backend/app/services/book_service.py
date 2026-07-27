"""
Book upload business logic.

Deliberately does NOT do full text extraction — that's Phase 4's job
(book parsing) and belongs on a Celery worker once files get large.
This phase only extracts metadata that's cheap to read synchronously
(title/author from document properties, page count for PDFs) so the
upload request returns fast.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.storage import get_storage
from app.models.book import Book, BookStatus

logger = get_logger(__name__)


class BookValidationError(Exception):
    """Raised for any upload rejection the endpoint should turn into a 400."""


@dataclass
class ExtractedMetadata:
    title: str
    author: str | None = None
    page_count: int | None = None


def validate_upload(file: UploadFile, size_bytes: int) -> str:
    """Returns the lowercase extension if valid, else raises BookValidationError."""
    extension = Path(file.filename or "").suffix.lstrip(".").lower()

    allowed_extensions = settings.get_allowed_upload_extensions()
    if extension not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        raise BookValidationError(f"Unsupported file type '.{extension}'. Allowed: {allowed}")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise BookValidationError(
            f"File is {size_bytes / 1024 / 1024:.1f}MB, which exceeds the "
            f"{settings.MAX_UPLOAD_SIZE_MB}MB limit."
        )
    if size_bytes == 0:
        raise BookValidationError("Uploaded file is empty.")

    return extension


def extract_metadata(extension: str, content: bytes, fallback_filename: str) -> ExtractedMetadata:
    """Best-effort metadata read. Any parser failure falls back to the
    filename as the title rather than failing the whole upload — a
    malformed document property block shouldn't block someone from
    uploading their book."""
    fallback_title = Path(fallback_filename).stem

    try:
        if extension == "pdf":
            return _extract_pdf_metadata(content, fallback_title)
        if extension == "docx":
            return _extract_docx_metadata(content, fallback_title)
        if extension == "epub":
            return _extract_epub_metadata(content, fallback_title)
    except Exception as exc:  # noqa: BLE001 - metadata extraction must never block upload
        logger.error(f"metadata_extraction_failed: {extension} - {exc}")

    return ExtractedMetadata(title=fallback_title)


def _extract_pdf_metadata(content: bytes, fallback_title: str) -> ExtractedMetadata:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    info = reader.metadata or {}
    return ExtractedMetadata(
        title=(info.title or fallback_title) if info else fallback_title,
        author=info.author if info else None,
        page_count=len(reader.pages),
    )


def _extract_docx_metadata(content: bytes, fallback_title: str) -> ExtractedMetadata:
    from docx import Document

    doc = Document(BytesIO(content))
    props = doc.core_properties
    return ExtractedMetadata(
        title=props.title or fallback_title,
        author=props.author or None,
    )


def _extract_epub_metadata(content: bytes, fallback_title: str) -> ExtractedMetadata:
    import ebooklib
    from ebooklib import epub

    book = epub.read_epub(BytesIO(content), options={"ignore_ncx": True})
    titles = book.get_metadata("DC", "title")
    creators = book.get_metadata("DC", "creator")
    return ExtractedMetadata(
        title=titles[0][0] if titles else fallback_title,
        author=creators[0][0] if creators else None,
    )


def create_book(db: Session, owner_id: uuid.UUID, file: UploadFile, content: bytes) -> Book:
    extension = validate_upload(file, len(content))
    metadata = extract_metadata(extension, content, file.filename or "untitled")

    storage_key = f"books/{owner_id}/{uuid.uuid4()}.{extension}"
    get_storage().save(storage_key, BytesIO(content))

    book = Book(
        owner_id=owner_id,
        title=metadata.title,
        author=metadata.author,
        original_filename=file.filename or "untitled",
        file_extension=extension,
        file_size_bytes=len(content),
        storage_key=storage_key,
        page_count=metadata.page_count,
        status=BookStatus.UPLOADED,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    logger.info(f"book_uploaded: {book.id} owner={owner_id} ext={extension}")
    return book


def list_books(db: Session, owner_id: uuid.UUID) -> list[Book]:
    return list(
        db.execute(
            select(Book).where(Book.owner_id == owner_id).order_by(Book.created_at.desc())
        ).scalars()
    )


def get_book(db: Session, owner_id: uuid.UUID, book_id: uuid.UUID) -> Book | None:
    return db.execute(
        select(Book).where(Book.id == book_id, Book.owner_id == owner_id)
    ).scalar_one_or_none()