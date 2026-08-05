"""
Chunking background job. Triggered automatically the moment a book's
status becomes PARSED (see parsing_tasks.parse_book_task) — chunking
itself is fast (no external API calls, no OCR), but it's still a
separate Celery task rather than inline in the parse task so each job
stays focused on one thing and can be retried/observed independently.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.book import Book, BookStatus
from app.models.chapter import Chapter
from app.models.chunk import Chunk
from app.services.chunking.chunker import chunk_chapter

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="chunk_book",
    autoretry_for=(ConnectionError, OSError),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def chunk_book_task(self, book_id: str) -> None:
    db: Session = SessionLocal()
    try:
        book = db.get(Book, book_id)
        if book is None:
            logger.error(f"chunk_book_task: book {book_id} not found")
            return

        book.status = BookStatus.CHUNKING
        book.error_message = None
        db.commit()

        chapters = list(
            db.execute(
                select(Chapter).where(Chapter.book_id == book.id).order_by(Chapter.chapter_index)
            ).scalars()
        )

        if not chapters:
            book.status = BookStatus.FAILED
            book.error_message = "No chapters were found to chunk. Parsing may have failed silently."
            db.commit()
            return

        # Replace any previous chunks (supports re-chunking, e.g. after
        # CHUNK_MAX_TOKENS is tuned).
        db.query(Chunk).filter(Chunk.book_id == book.id).delete()

        total_chunks = 0
        for chapter in chapters:
            chunks = chunk_chapter(chapter.content)
            for index, chunk in enumerate(chunks):
                db.add(
                    Chunk(
                        book_id=book.id,
                        chapter_id=chapter.id,
                        chunk_index=index,
                        content=chunk.content,
                        token_count=chunk.token_count,
                        char_count=chunk.char_count,
                        context_snippet=chunk.context_snippet,
                    )
                )
            total_chunks += len(chunks)

        book.status = BookStatus.CHUNKED
        db.commit()
        logger.info(f"chunk_book_succeeded: {book_id} chapters={len(chapters)} chunks={total_chunks}")

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        book = db.get(Book, book_id)
        if book is not None:
            book.status = BookStatus.FAILED
            book.error_message = "Chunking failed due to an unexpected error."
            db.commit()
        logger.error(f"chunk_book_unexpected_error: {book_id} - {exc}")
        raise
    finally:
        db.close()
