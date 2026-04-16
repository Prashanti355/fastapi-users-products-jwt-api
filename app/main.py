from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions.base import AppException
from app.core.handlers.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
)
from app.core.logging_config import setup_logging
from app.core.rate_limit import limiter
from app.core.request_logging_middleware import RequestLoggingMiddleware


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Users & Products API",
    description=(
        "API REST con gestión de usuarios, productos y autenticación JWT. "
        "Use el botón Authorize para iniciar sesión desde Swagger."
    ),
    version="3.0.0",
    debug=settings.DEBUG,
    swagger_ui_init_oauth={},
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
    expose_headers=["Authorization"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Salud"])
async def root():
    return {
        "mensaje": "¡Bienvenido a la Users & Products API!",
        "estado": "Operativa",
        "version": "3.0.0",
        "login": "/api/v1/auth/login",
    }


@app.get("/health", tags=["Salud"])
async def health_check():
    return {"status": "healthy"}