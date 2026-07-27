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
from app.schemas.book import BookListOut, BookOut
from app.services.book_service import BookValidationError, create_book, get_book, list_books

router = APIRouter(prefix="/books")
logger = get_logger(__name__)


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
    book = get_book(db, current_user.id, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book