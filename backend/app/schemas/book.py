"""Request/response contracts for the book upload endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.book import BookStatus
from app.models.chunk import ChunkStatus

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
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BookListOut(BaseModel):
    items: list[BookOut]
    total: int

class ChapterOut(BaseModel):
    id: uuid.UUID
    chapter_index: int
    title: str
    word_count: int
 
    model_config = {"from_attributes": True}
 
 
class ChapterDetailOut(ChapterOut):
    content: str
 
 
class ChapterListOut(BaseModel):
    items: list[ChapterOut]
    total: int

class ChunkOut(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    chunk_index: int
    token_count: int
    char_count: int
    status: ChunkStatus

    model_config = {"from_attributes": True}


class ChunkDetailOut(ChunkOut):
    content: str
    context_snippet: str | None
    error_message: str | None


class ChunkListOut(BaseModel):
    items: list[ChunkOut]
    total: int
    total_tokens: int