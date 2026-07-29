"""
Database engine + session factory + FastAPI dependency.

Import `get_db` in any endpoint that needs DB access:

    from fastapi import Depends
    from app.db.session import get_db

    @router.get("/books")
    def list_books(db: Session = Depends(get_db)):
        ...
"""

from collections.abc import Generator
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models import book, chapter, user  # noqa: F401

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres") and "://" in DATABASE_URL:
    try:
        create_engine(DATABASE_URL, pool_pre_ping=True, future=True).connect().close()
    except Exception:
        DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # avoids "server closed the connection" errors
    future=True,
)
with engine.begin() as conn:
    conn.execute(text("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, full_name VARCHAR(255) NOT NULL, hashed_password VARCHAR(255), google_id VARCHAR(255), is_active BOOLEAN DEFAULT 1, is_verified BOOLEAN DEFAULT 0, created_at TIMESTAMP, updated_at TIMESTAMP)"))
    Base.metadata.create_all(bind=conn)

    # If the app is started against an older database schema, ensure new
    # columns added by later migrations are present. This particularly helps
    # local/dev Postgres instances that were created before the book
    # error_message column existed.
    from sqlalchemy import inspect

    inspector = inspect(conn)
    if inspector.has_table("books"):
        columns = {col["name"] for col in inspector.get_columns("books")}
        if "error_message" not in columns:
            conn.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS error_message VARCHAR(1000)"))

        status_column = next(
            (col for col in inspector.get_columns("books") if col["name"] == "status"),
            None,
        )
        if status_column is not None:
            status_type = str(status_column.get("type"))
            if "ENUM" in status_type.upper() or "BOOK_STATUS" in status_type.upper():
                conn.execute(
                    text(
                        "ALTER TABLE books ALTER COLUMN status TYPE VARCHAR(20) USING status::text"
                    )
                )
                conn.execute(text("ALTER TABLE books ALTER COLUMN status SET DEFAULT 'uploaded'"))

    Base.metadata.create_all(bind=conn)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:  # Session: if not Generator
    """FastAPI dependency: yields a session, always closes it after the request."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()