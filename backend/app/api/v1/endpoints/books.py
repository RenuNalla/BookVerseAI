"""
/api/v1/books/* endpoints.

upload -> validates + stores the file, extracts light metadata, creates
          a Book row with status=UPLOADED. Parsing the actual text
          content happens in Phase 4 (as a background job, once files
          can be large enough that synchronous parsing would time out
          the request).
list   -> the current user's books, newest first.
detail -> a single book the current user owns.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.book import (
    BookListOut,
    BookOut, 
    ChapterDetailOut, 
    ChapterListOut,
    ChunkDetailOut,
    ChunkListOut
)
from app.services.book_service import (
    BookValidationError, 
    create_book, 
    get_book,
    get_chapter,
    get,
    get_chunk,
    list_books_chunk, 
    list_books,
    list_chapters,
    reparse_book,
    list_chunks,
    list_chunks_for_chapter,
    rechunk_book,
    reparse_book,
)


router = APIRouter(prefix="/books")
logger = get_logger(__name__)

def _get_owned_book_or_404(db: Session, current_user: User, book_id: uuid.UUID):
    book = get_book(db, current_user.id, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.post("/upload", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def upload_book(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        book = create_book(db, current_user.id, file, content)
    except BookValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return book


@router.get("", response_model=BookListOut)
def get_books(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    books = list_books(db, current_user.id)
    return BookListOut(items=books, total=len(books))


@router.get("/{book_id}", response_model=BookOut)
def get_book_detail(
    book_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_book_or_404(db, current_user, book_id)
    # book = get_book(db, current_user.id, book_id)
    # if book is None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    # return book

@router.post("/{book_id}/reparse", response_model=BookOut)
def reparse_book_endpoint(
    book_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-runs parsing — useful if a book landed in FAILED status and the
    underlying cause (e.g. missing OCR dependency) has since been fixed."""
    book = _get_owned_book_or_404(db, current_user, book_id)
    reparse_book(db, book)
    return book
 
 
@router.get("/{book_id}/chapters", response_model=ChapterListOut)
def get_book_chapters(
    book_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    book = _get_owned_book_or_404(db, current_user, book_id)
    chapters = list_chapters(db, book)
    return ChapterListOut(items=chapters, total=len(chapters))
 
 
@router.get("/{book_id}/chapters/{chapter_id}", response_model=ChapterDetailOut)
def get_book_chapter_detail(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    book = _get_owned_book_or_404(db, current_user, book_id)
    chapter = get_chapter(db, book, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    return chapter

@router.post("/{book_id}/rechunk", response_model=BookOut)
def rechunk_book_endpoint(
    book_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-runs chunking — useful after a FAILED chunking run, or after
    tuning CHUNK_MAX_TOKENS and wanting existing books re-chunked."""
    book = _get_owned_book_or_404(db, current_user, book_id)
    rechunk_book(db, book)
    return book


@router.get("/{book_id}/chunks", response_model=ChunkListOut)
def get_book_chunks(
    book_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    book = _get_owned_book_or_404(db, current_user, book_id)
    chunks = list_chunks(db, book)
    return ChunkListOut(items=chunks, total=len(chunks), total_tokens=sum(c.token_count for c in chunks))


@router.get("/{book_id}/chapters/{chapter_id}/chunks", response_model=ChunkListOut)
def get_chapter_chunks(
    book_id: uuid.UUID,
    chapter_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    book = _get_owned_book_or_404(db, current_user, book_id)
    chapter = get_chapter(db, book, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    chunks = list_chunks_for_chapter(db, chapter.id)
    return ChunkListOut(items=chunks, total=len(chunks), total_tokens=sum(c.token_count for c in chunks))

@router.get("/{book_id}/chunks/{chunk_id}", response_model=ChunkDetailOut)
def get_chunk_detail(
    book_id: uuid.UUID,
    chunk_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    book = _get_owned_book_or_404(db, current_user, book_id)
    chunk = get_chunk(db, book, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return chunk
