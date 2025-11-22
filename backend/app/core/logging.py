from __future__ import annotations

import json
import logging
from logging import LogRecord
from typing import Any

from app.core import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:  # pragma: no cover - formatting
        base: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)


def configure_logging() -> None:
    if not settings.structured_logging:
        logging.basicConfig(level=settings.log_level)
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level)


__all__ = ["configure_logging", "JsonFormatter"]
