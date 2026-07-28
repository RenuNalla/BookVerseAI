"""
Auth flow tests. Uses an in-memory SQLite DB (via dependency override) so
tests never touch the real Postgres instance and run fast in CI.
"""

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


def test_register_then_login():
    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "full_name": "Test User", "password": "supersecret"},
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["email"] == "test@example.com"

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "supersecret"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens


def test_duplicate_registration_rejected():
    payload = {"email": "dup@example.com", "full_name": "Dup", "password": "supersecret"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_wrong_password_rejected():
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@example.com", "full_name": "W", "password": "correcthorse"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "incorrect"},
    )
    assert resp.status_code == 401


def test_me_requires_token():
    assert client.get("/api/v1/auth/me").status_code in (401, 403)


def test_me_with_valid_token():
    client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "full_name": "Me", "password": "supersecret"},
    )
    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "supersecret"},
    ).json()

    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_refresh_token_flow():
    client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "full_name": "R", "password": "supersecret"},
    )
    tokens = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "supersecret"},
    ).json()

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()