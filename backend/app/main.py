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
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import api_router
from app.db.base import Base
from app.db.session import engine
from app.models import book, user  # noqa: F401

# Configure logging as early as possible so startup events are captured.
configure_logging()
logger = get_logger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup_complete", extra={"env": settings.ENVIRONMENT})
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="AI Book Translation Platform - Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
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

# Only relevant when STORAGE_BACKEND=local (the dev default). In that mode,
# LocalStorageBackend.url_for() returns "/files/<key>" — this mount is what
# actually serves those bytes. Not used at all when STORAGE_BACKEND=s3,
# since S3 URLs point straight at the bucket.
if settings.STORAGE_BACKEND == "local":
    Path(settings.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    app.mount("/files", StaticFiles(directory=settings.LOCAL_STORAGE_PATH), name="files")

#@app.on_event("startup")
#async def on_startup() -> None:
#    logger.info("startup_complete", extra={"env": settings.ENVIRONMENT})

@app.get("/", tags=["root"])
def root() -> dict:
    """Simple landing endpoint so hitting the base URL doesn't 404."""
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
    }