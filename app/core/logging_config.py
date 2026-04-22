from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

from app.core.config import settings


LOG_DIR = Path(settings.LOG_DIR)
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | request_id=%(request_id)s | "
    "method=%(method)s | path=%(path)s | status=%(status_code)s | "
    "latency_ms=%(latency_ms)s | client_ip=%(client_ip)s | %(message)s"
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        defaults = {
            "request_id": "-",
            "method": "-",
            "path": "-",
            "status_code": "-",
            "latency_ms": "-",
            "client_ip": "-",
        }

        for field_name, default_value in defaults.items():
            if not hasattr(record, field_name):
                setattr(record, field_name, default_value)

        return True


def _build_file_handler(filename: str, level: int) -> RotatingFileHandler:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.addFilter(RequestContextFilter())
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def setup_logging() -> None:
    technical_logger = logging.getLogger("app.technical")
    error_logger = logging.getLogger("app.error")

    technical_configured = getattr(technical_logger, "_configured", False)
    error_configured = getattr(error_logger, "_configured", False)

    if technical_configured and error_configured:
        return

    if not technical_configured:
        technical_logger.setLevel(logging.INFO)
        technical_logger.propagate = False
        technical_logger.addHandler(
            _build_file_handler("technical.log", logging.INFO)
        )
        technical_logger._configured = True

    if not error_configured:
        error_logger.setLevel(logging.ERROR)
        error_logger.propagate = False
        error_logger.addHandler(
            _build_file_handler("error.log", logging.ERROR)
        )
        error_logger._configured = True