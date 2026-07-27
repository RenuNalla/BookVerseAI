"""Request/response contracts for the book upload endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.book import BookStatus


class BookOut(BaseModel):
    id: uuid.UUID
    title: str
    author: str | None
    original_filename: str
    file_extension: str
    file_size_bytes: int
    page_count: int | None
    source_language: str
    status: BookStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class BookListOut(BaseModel):
    items: list[BookOut]
    total: int