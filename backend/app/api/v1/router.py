"""
Aggregates every endpoint module under app/api/v1/endpoints/ into a single
router that main.py mounts once. Future phases add one line here per
new endpoint module (auth, books, translation, ...) — main.py never
changes again.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health,auth, books

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(books.router, tags=["books"])