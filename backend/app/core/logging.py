"""
Logging configuration.

Uses Python's stdlib logging with a JSON-ish formatter so logs are easy
to parse in CloudWatch / Azure Monitor / ELK later. Call configure_logging()
once at startup; call get_logger(__name__) everywhere else.
"""

import logging
import sys

from app.core.config import settings


class RequestFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = (
            f'{{"time": "{self.formatTime(record)}", '
            f'"level": "{record.levelname}", '
            f'"logger": "{record.name}", '
            f'"message": "{record.getMessage()}"}}'
        )
        return base


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Avoid duplicate handlers on reload
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(RequestFormatter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)