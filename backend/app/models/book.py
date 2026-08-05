"""
Book ORM model. Represents one uploaded source file. Translated copies
(Phase 6) will reference back to this row via a `source_book_id` FK added
in that phase — kept out for now so this migration stays focused.
"""


import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base

class BookStatus(str, enum.Enum):
    UPLOADED = "uploaded"          # file stored, nothing processed yet
    PARSING = "parsing"            # Phase 4 text extraction in progress
    PARSED = "parsed"
    CHUNKING = "chunking"          # Phase 5 chunking in progress
    CHUNKED = "chunked"            # ready for translation
    TRANSLATING = "translating"    # Phase 6
    READY = "ready"
    FAILED = "failed"


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)

    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Populated where cheaply available at upload time (e.g. PDF page count).
    # Full text/chapter extraction happens in Phase 4, not here.
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_language: Mapped[str] = mapped_column(String(10), default="en")
    status: Mapped[BookStatus] = mapped_column(String(20), default=BookStatus.UPLOADED, nullable=False)

    # Populated only when status == FAILED, surfaced to the frontend so
    # the user sees *why* parsing failed instead of a silent stuck state.
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now()
    )
