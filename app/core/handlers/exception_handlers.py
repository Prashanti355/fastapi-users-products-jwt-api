from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions.base import AppException
from app.schemas.response import ApiError


async def app_exception_handler(
    request: Request,
    exc: AppException
):
    payload = ApiError(
        codigo=exc.code,
        mensaje=exc.message,
        resultado=exc.result
    ).model_dump()

    return JSONResponse(
        status_code=exc.code,
        content=jsonable_encoder(payload)
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    payload = ApiError(
        codigo=400,
        mensaje="Datos inválidos",
        resultado=exc.errors()
    ).model_dump()

    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(payload)
    )