"""
Book parsing background job.

Triggered right after upload (see book_service.create_book, Phase 3) so
the user never has to manually kick off parsing. Runs on the `worker`
container, not the API process — the API stays responsive to other
requests while a slow OCR job grinds through a scanned PDF.

Retries automatically on transient failures (e.g. the DB briefly
unreachable during a deploy); does NOT retry on a genuinely corrupt
file, since retrying won't fix that — it marks the book FAILED with a
message instead.
"""

from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.core.storage import get_storage
from app.db.session import SessionLocal
from app.models.book import Book,BookStatus
from app.models.chapter import Chapter
from app.services.parsing.orchestrator import parse_book_content

logger = get_logger(__name__)


class BookParsingError(Exception):
    """Raised for failures that are the file's fault, not transient
    infra — these should NOT be retried."""


@celery_app.task(
    bind=True,
    name="parse_book",
    autoretry_for=(ConnectionError, OSError),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def parse_book_task(self: Task, book_id: str) -> None:
    db: Session = SessionLocal()
    try:
        book = db.get(Book, book_id)
        if book is None:
            logger.error(f"parse_book_task: book {book_id} not found")
            return

        book.status = BookStatus.PARSING
        book.error_message = None
        db.commit()

        try:
            content = _read_book_bytes(book)
            chapters = parse_book_content(book.file_extension, content)
            if not chapters:
                raise BookParsingError("No extractable text found in this file.")
        except BookParsingError as exc:
            book.status = BookStatus.FAILED
            book.error_message = str(exc)
            db.commit()
            logger.error(f"parse_book_failed: {book_id} - {exc}")
            return

        # Replace any previous chapters (supports re-parsing after a fix).
        db.query(Chapter).filter(Chapter.book_id == book.id).delete()
        for index, chapter in enumerate(chapters):
            db.add(
                Chapter(
                    book_id=book.id,
                    chapter_index=index,
                    title=chapter.title[:500],
                    content=chapter.content,
                    word_count=chapter.word_count,
                )
            )

        book.status = BookStatus.PARSED
        db.commit()
        logger.info(f"parse_book_succeeded: {book_id} chapters={len(chapters)}")

        # Chunking has no reason to wait for a separate user action —
        # a parsed book with no chunks isn't useful for anything yet.
        from app.tasks.chunking_tasks import chunk_book_task

        chunk_book_task.delay(book_id)

    except Exception as exc:  # noqa: BLE001 - last-resort guard so status never gets stuck
        db.rollback()
        book = db.get(Book, book_id)
        if book is not None:
            book.status = BookStatus.FAILED
            book.error_message = "Parsing failed due to an unexpected error."
            db.commit()
        logger.error(f"parse_book_unexpected_error: {book_id} - {exc}")
        raise
    finally:
        db.close()


def _read_book_bytes(book: Book) -> bytes:
    """Reads the original uploaded file back from storage. Only
    implemented for the local backend today — S3StorageBackend would
    need a download method added alongside this when that's wired up."""
    from app.core.config import settings

    if settings.STORAGE_BACKEND == "local":
        path = f"{settings.LOCAL_STORAGE_PATH}/{book.storage_key}"
        with open(path, "rb") as f:
            return f.read()

    storage = get_storage()
    # S3StorageBackend doesn't have a `download` method yet — added when
    # Phase 14 (deployment) actually switches STORAGE_BACKEND to s3.
    raise NotImplementedError(
        f"Reading book bytes back from '{settings.STORAGE_BACKEND}' storage isn't implemented yet."
    )