"""
Translation domain models.

TranslationJob: one row per "translate this book to this language"
request. Tracks aggregate progress (total/completed/failed chunk
counts) so the frontend can poll ONE row instead of counting chunk
statuses itself on every request.

ChunkTranslation: one row per (chunk, job) — the actual translated text.
Deliberately a separate table from Chunk rather than columns on it,
because a book can be translated to MULTIPLE target languages over time,
and each needs its own independent status/retry lifecycle.

TranslationMemory: cross-job, cross-book cache of (source text hash,
source lang, target lang) -> translated text. Cost optimization — see
services/translation/memory.py for the hashing scheme.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class TranslationJobStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"        # every chunk translated successfully
    PARTIAL = "partial"            # some chunks failed, some succeeded
    FAILED = "failed"              # every chunk failed, or job-level fatal error
    REJECTED = "rejected"          # never started — failed cost/quota check


class ChunkTranslationStatus(str, enum.Enum):
    PENDING = "pending"
    TRANSLATING = "translating"
    TRANSLATED = "translated"
    FAILED = "failed"


class TranslationJob(Base):
    __tablename__ = "translation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    source_language: Mapped[str] = mapped_column(String(10), nullable=False)
    target_language: Mapped[str] = mapped_column(String(10), nullable=False)

    status: Mapped[TranslationJobStatus] = mapped_column(
        Enum(TranslationJobStatus, name="translation_job_status"),
        default=TranslationJobStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    completed_chunks: Mapped[int] = mapped_column(Integer, default=0)
    failed_chunks: Mapped[int] = mapped_column(Integer, default=0)

    # Sum of tokens_used across every provider call this job made,
    # including cache misses only (memory hits cost nothing) — this is
    # the number usage_logging/cost tracking should read.
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    memory_hits: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChunkTranslation(Base):
    __tablename__ = "chunk_translations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("translation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    translated_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ChunkTranslationStatus] = mapped_column(
        Enum(ChunkTranslationStatus, name="chunk_translation_status"),
        default=ChunkTranslationStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    from_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class TranslationMemory(Base):
    __tablename__ = "translation_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # sha256 of normalized(source_text) + source_language + target_language.
    # Unique so a duplicate insert is a straightforward upsert-or-skip.
    memory_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    source_language: Mapped[str] = mapped_column(String(10), nullable=False)
    target_language: Mapped[str] = mapped_column(String(10), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)

    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
