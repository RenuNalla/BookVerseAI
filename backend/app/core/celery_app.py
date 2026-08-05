"""
Celery application instance.

This is the FIRST background job in the project — book parsing is slow
enough (OCR especially) that doing it inline on the upload request would
time out. From here on, "slow" work goes through Celery: parsing (this
phase), chunking (Phase 5), translation (Phase 6), TTS (Phase 8), image
generation (Phase 9).

Started via: celery -A app.core.celery_app worker --loglevel=info
(see the `worker` service in docker-compose.yml)
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "book_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.parsing_tasks", "app.tasks.chunking_tasks", "app.tasks.translation_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # A parsing job holding a worker slot forever (corrupt file, OCR hang)
    # shouldn't be able to starve the queue — hard cap per task.
    task_time_limit=15 * 60,
    task_soft_time_limit=12 * 60,
    # One book at a time per worker process: parsing is CPU/IO heavy, and
    # prefetching more just delays other users' books for no benefit.
    worker_prefetch_multiplier=1,
)
# In non-production (tests/dev) run tasks eagerly to avoid requiring Redis.
if settings.ENVIRONMENT != "production":
    celery_app.conf.task_always_eager = True