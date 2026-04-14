from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.exceptions.base import AppException
from app.core.handlers.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
)

app = FastAPI(
    title="Users & Products API",
    description=(
        "API REST con gestión de usuarios, productos y autenticación JWT. "
        "Use el botón Authorize para iniciar sesión desde Swagger."
    ),
    version="3.0.0",
    debug=settings.DEBUG,
    swagger_ui_init_oauth={},
)


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Salud"])
async def root():
    return {
        "mensaje": "¡Bienvenido a la Users & Products API!",
        "estado": "Operativa",
        "version": "3.0.0",
        "login": "/api/v1/auth/login"
    }


@app.get("/health", tags=["Salud"])
async def health_check():
    return {"status": "healthy"}