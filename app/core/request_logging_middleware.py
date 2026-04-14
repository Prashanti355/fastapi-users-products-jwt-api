import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


technical_logger = logging.getLogger("app.technical")
error_logger = logging.getLogger("app.error")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "-"

        try:
            response = await call_next(request)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            technical_logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "client_ip": client_ip,
                },
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            error_logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "latency_ms": latency_ms,
                    "client_ip": client_ip,
                },
            )
            raise