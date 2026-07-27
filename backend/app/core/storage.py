"""
Storage backend abstraction.

Every other part of the app calls `get_storage()` and only ever sees
`save(key, file_obj)` / `url_for(key)` / `delete(key)`. Which concrete
backend is used (local disk vs S3) is decided ONCE here from
settings.STORAGE_BACKEND — nothing else in the codebase imports boto3
or touches the filesystem directly. This is what lets Phase 3 run with
zero AWS setup today and swap to real S3 later by changing one env var.
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, file_obj: BinaryIO) -> None: ...

    @abstractmethod
    def url_for(self, key: str) -> str: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalStorageBackend(StorageBackend):
    """Writes to a local directory. Used by default so `docker compose up`
    works with no cloud account. Not suitable for a real multi-instance
    production deployment — switch to S3StorageBackend for that."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, file_obj: BinaryIO) -> None:
        destination = self.base_path / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "wb") as out:
            shutil.copyfileobj(file_obj, out)

    def url_for(self, key: str) -> str:
        # Served via the /files static mount registered in main.py.
        return f"/files/{key}"

    def delete(self, key: str) -> None:
        target = self.base_path / key
        if target.exists():
            target.unlink()


class S3StorageBackend(StorageBackend):
    """Real cloud storage. Requires boto3 and valid AWS_* credentials
    in settings. Not exercised by default/local dev — flip
    STORAGE_BACKEND=s3 once credentials are available."""

    def __init__(self):
        import boto3  # imported lazily so `boto3` isn't a hard dependency in local dev

        self.bucket = settings.S3_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

    def save(self, key: str, file_obj: BinaryIO) -> None:
        self.client.upload_fileobj(file_obj, self.bucket, key)

    def url_for(self, key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=3600,
        )

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend()
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageBackend(settings.LOCAL_STORAGE_PATH)
    raise ValueError(f"Unsupported STORAGE_BACKEND: {settings.STORAGE_BACKEND}")
