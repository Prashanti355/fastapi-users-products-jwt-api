from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_auth_service, get_current_active_user
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    PublicRegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.response import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Autentica al usuario y devuelve un access token y un refresh token."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Endpoint compatible con OAuth2/Swagger.
    Recibe credenciales como formulario, no como JSON.
    """
    login_data = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )

    return await auth_service.login(
        db,
        login_data=login_data
    )


@router.post(
    "/register",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    description="Crea un nuevo usuario y devuelve tokens JWT inmediatamente."
)
async def register(
    user_data: PublicRegisterRequest = Body(
        ...,
        description="Datos públicos del nuevo usuario"
    ),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.register(
        db,
        user_data=user_data
    )

    return ApiResponse[TokenResponse](
        codigo=201,
        mensaje="Usuario registrado y autenticado correctamente.",
        resultado=tokens
    )


@router.post(
    "/refresh-token",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Refrescar tokens",
    description="Genera un nuevo par de tokens usando un refresh token válido."
)
async def refresh_token(
    refresh_data: RefreshTokenRequest = Body(
        ...,
        description="Refresh token válido"
    ),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.refresh_token(
        db,
        refresh_token=refresh_data.refresh_token
    )

    return ApiResponse[TokenResponse](
        codigo=200,
        mensaje="Tokens renovados correctamente.",
        resultado=tokens
    )


@router.get(
    "/me",
    response_model=ApiResponse[CurrentUser],
    status_code=status.HTTP_200_OK,
    summary="Obtener usuario autenticado",
    description="Retorna los datos del usuario autenticado actual."
)
async def me(
    current_user: CurrentUser = Depends(get_current_active_user),
):
    return ApiResponse[CurrentUser](
        codigo=200,
        mensaje="Usuario autenticado obtenido exitosamente.",
        resultado=current_user
    )