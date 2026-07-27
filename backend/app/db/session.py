"""
Database engine + session factory + FastAPI dependency.

Import `get_db` in any endpoint that needs DB access:

    from fastapi import Depends
    from app.db.session import get_db

    @router.get("/books")
    def list_books(db: Session = Depends(get_db)):
        ...
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, session
from collections.abc import Generator


from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # avoids "server closed the connection" errors
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

def get_db() -> Generator[Session, None, None]: #Session: if not Generator
    """FastAPI dependency: yields a session, always closes it after the request."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()