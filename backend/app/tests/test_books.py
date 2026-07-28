"""
Book upload tests. Reuses the same in-memory-SQLite pattern as
test_auth.py, and overrides the storage backend to write into a temp
directory so tests never touch the real ./storage folder.
"""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def temp_storage(tmp_path, monkeypatch):
    """Redirects the local storage backend to a pytest tmp dir."""
    from app.core import config

    monkeypatch.setattr(config.settings, "LOCAL_STORAGE_PATH", str(tmp_path))
    yield tmp_path


def _register_and_login(email: str = "uploader@example.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Uploader", "password": "supersecret"},
    )
    tokens = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret"}
    ).json()
    return tokens["access_token"]


def test_upload_txt_book_succeeds(temp_storage):
    token = _register_and_login()
    file_content = b"Chapter 1. Once upon a time..."

    resp = client.post(
        "/api/v1/books/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("my_story.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "my_story"
    assert body["file_extension"] == "txt"
    assert body["status"] == "uploaded"


def test_upload_rejects_disallowed_extension(temp_storage):
    token = _register_and_login()
    resp = client.post(
        "/api/v1/books/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("malware.exe", io.BytesIO(b"data"), "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_upload_requires_auth(temp_storage):
    resp = client.post(
        "/api/v1/books/upload",
        files={"file": ("book.txt", io.BytesIO(b"data"), "text/plain")},
    )
    assert resp.status_code in (401, 403)


def test_list_books_scoped_to_owner(temp_storage):
    token_a = _register_and_login("a@example.com")
    token_b = _register_and_login("b@example.com")

    client.post(
        "/api/v1/books/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("a_book.txt", io.BytesIO(b"content"), "text/plain")},
    )

    resp_a = client.get("/api/v1/books", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.get("/api/v1/books", headers={"Authorization": f"Bearer {token_b}"})

    assert resp_a.json()["total"] == 1
    assert resp_b.json()["total"] == 0