from types import SimpleNamespace

import pytest
from starlette.responses import Response

from app.core.request_logging_middleware import RequestLoggingMiddleware


@pytest.mark.asyncio
async def test_request_logging_middleware_logs_success_and_sets_request_id_header(mocker):
    middleware = RequestLoggingMiddleware(app=lambda scope, receive, send: None)

    request = SimpleNamespace(
        state=SimpleNamespace(),
        client=SimpleNamespace(host="127.0.0.1"),
        method="GET",
        url=SimpleNamespace(path="/api/v1/test"),
    )

    response = Response(content="ok", status_code=200)
    call_next = mocker.AsyncMock(return_value=response)

    mocker.patch(
        "app.core.request_logging_middleware.uuid4",
        return_value="req-123",
    )
    mocker.patch(
        "app.core.request_logging_middleware.time.perf_counter",
        side_effect=[10.0, 10.25],
    )
    technical_logger_info = mocker.patch(
        "app.core.request_logging_middleware.technical_logger.info"
    )
    error_logger_exception = mocker.patch(
        "app.core.request_logging_middleware.error_logger.exception"
    )

    result = await middleware.dispatch(request, call_next)

    assert result is response
    assert request.state.request_id == "req-123"
    assert result.headers["X-Request-ID"] == "req-123"

    call_next.assert_awaited_once_with(request)
    technical_logger_info.assert_called_once_with(
        "Request completed",
        extra={
            "request_id": "req-123",
            "method": "GET",
            "path": "/api/v1/test",
            "status_code": 200,
            "latency_ms": 250.0,
            "client_ip": "127.0.0.1",
        },
    )
    error_logger_exception.assert_not_called()


@pytest.mark.asyncio
async def test_request_logging_middleware_logs_exception_and_reraises(mocker):
    middleware = RequestLoggingMiddleware(app=lambda scope, receive, send: None)

    request = SimpleNamespace(
        state=SimpleNamespace(),
        client=None,
        method="POST",
        url=SimpleNamespace(path="/api/v1/fail"),
    )

    call_next = mocker.AsyncMock(side_effect=RuntimeError("boom"))

    mocker.patch(
        "app.core.request_logging_middleware.uuid4",
        return_value="req-456",
    )
    mocker.patch(
        "app.core.request_logging_middleware.time.perf_counter",
        side_effect=[20.0, 20.5],
    )
    technical_logger_info = mocker.patch(
        "app.core.request_logging_middleware.technical_logger.info"
    )
    error_logger_exception = mocker.patch(
        "app.core.request_logging_middleware.error_logger.exception"
    )

    with pytest.raises(RuntimeError, match="boom"):
        await middleware.dispatch(request, call_next)

    assert request.state.request_id == "req-456"

    call_next.assert_awaited_once_with(request)
    technical_logger_info.assert_not_called()
    error_logger_exception.assert_called_once_with(
        "Unhandled exception",
        extra={
            "request_id": "req-456",
            "method": "POST",
            "path": "/api/v1/fail",
            "status_code": 500,
            "latency_ms": 500.0,
            "client_ip": "-",
        },
    )