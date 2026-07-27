"""
Health check endpoint.

Used by: Docker HEALTHCHECK, load balancers, uptime monitors, and the
Angular frontend on app boot (to show a "backend unreachable" banner).

Returns 200 with component-level status even when a dependency is down,
so the caller can distinguish "API is up but DB is down" from "API is
completely unreachable" (which would be a connection error, not a 200).
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import engine

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
def health_check() -> dict:
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - we want to report ANY failure
        logger.error(f"db_health_check_failed: {exc}")
        db_status = "unreachable"

    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "database": db_status,
        },
    }