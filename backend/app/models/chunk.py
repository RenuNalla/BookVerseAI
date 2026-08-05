"""
Chunk ORM model. One row per translation-sized unit of text, produced
from a Chapter by Phase 5's chunker. `book_id` is denormalized (also
reachable via chapter_id -> chapters.book_id) purely so "all chunks for
this book" queries — which Phase 6 does constantly — don't need a join.

`status` exists now, one phase early, specifically so Phase 6 can retry
a single failed chunk's translation without needing a schema change —
see the Production Release Addendum's requirement that a failed chunk
must not force retranslating the whole book.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class ChunkStatus(str, enum.Enum):
    READY = "ready"              # chunked, waiting to be translated
    TRANSLATING = "translating"  # Phase 6
    TRANSLATED = "translated"
    FAILED = "failed"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Tail of the previous chunk's text — a hint for the translation
    # prompt in Phase 6, not itself translated. See chunker.py.
    context_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ChunkStatus] = mapped_column(
        Enum(ChunkStatus, name="chunk_status"), default=ChunkStatus.READY, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
