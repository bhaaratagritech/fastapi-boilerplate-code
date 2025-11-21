from __future__ import annotations

import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Iterable, Optional

from .correlation import get_correlation_id
from ..utils.pii import scrub_pii


class ServiceJSONFormatter(logging.Formatter):
    """Format logs as JSON with correlation ID and optional PII scrubbing."""

    def __init__(self, pii_fields: Iterable[str]):
        super().__init__()
        self._pii_fields = list(pii_fields)

    def format(self, record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
            "function": record.funcName,
            "correlation_id": get_correlation_id("-"),
        }

        default_keys = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in default_keys and not key.startswith("_")
        }

        if extras:
            log_payload["extra"] = extras

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        scrubbed_payload = scrub_pii(log_payload, self._pii_fields)
        return json.dumps(scrubbed_payload, ensure_ascii=False)


class CorrelationIdFilter(logging.Filter):
    """Ensure correlation id is available on the log record for traditional formatters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id("-")
        return True


def configure_logging(level: str = "INFO", pii_fields: Optional[Iterable[str]] = None) -> None:
    """Configure root logging for the service."""
    pii_fields = pii_fields or ()
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation": {
                "()": CorrelationIdFilter,
            },
        },
        "formatters": {
            "json": {
                "()": ServiceJSONFormatter,
                "pii_fields": list(pii_fields),
            },
            "console": {
                "format": "%(asctime)s | %(levelname)s | %(correlation_id)s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "json",
                "filters": ["correlation"],
            },
        },
        "root": {
            "level": level,
            "handlers": ["default"],
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


