"""
Application entrypoint.

Responsible ONLY for:
  1. Creating the FastAPI instance
  2. Wiring up middleware (CORS, logging)
  3. Mounting the versioned API router
  4. Exposing a root-level health check

All business logic lives in services/, all DB access in db/ and models/,
all request/response contracts in schemas/. This file should stay thin.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import api_router

# Configure logging as early as possible so startup events are captured.
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="AI Book Translation Platform - Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS: allows the Angular dev server (http://localhost:4200) and the
# deployed frontend origin(s) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All versioned business endpoints (health, auth, books, ...) are mounted
# under /api/v1 via this single router. New phases add routers here.
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("startup_complete", extra={"env": settings.ENVIRONMENT})


@app.get("/", tags=["root"])
def root() -> dict:
    """Simple landing endpoint so hitting the base URL doesn't 404."""
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
    }