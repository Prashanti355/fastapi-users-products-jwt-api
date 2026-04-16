from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def rate_limit_key_func(request: Request) -> str:
    if settings.ENVIRONMENT == "testing":
        test_key = request.headers.get("X-Test-RateLimit-Key")
        if test_key:
            return f"test:{test_key}"

    return get_remote_address(request)


limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=settings.RATE_LIMIT_DEFAULTS,
    headers_enabled=settings.RATE_LIMIT_HEADERS_ENABLED,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    enabled=settings.RATE_LIMIT_ENABLED,
)