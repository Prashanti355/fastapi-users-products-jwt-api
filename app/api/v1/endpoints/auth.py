from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import (
    get_audit_log_service,
    get_auth_service,
    get_current_active_user,
)
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    PublicRegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.response import ApiResponse
from app.services.audit_log_service import AuditLogService
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
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
):
    login_data = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )

    tokens = await auth_service.login(
        db,
        login_data=login_data
    )

    current_user = await auth_service.get_current_user(db, token=tokens.access_token)

    await audit_log_service.log_event(
        db,
        action="login",
        entity="auth",
        actor=current_user,
        detail="Inicio de sesión exitoso."
    )

    return tokens


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
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
):
    tokens = await auth_service.register(
        db,
        user_data=user_data
    )

    current_user = await auth_service.get_current_user(db, token=tokens.access_token)

    await audit_log_service.log_event(
        db,
        action="register",
        entity="user",
        entity_id=str(current_user.id),
        actor=current_user,
        detail="Registro público de usuario exitoso."
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
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
):
    tokens = await auth_service.refresh_token(
        db,
        refresh_token=refresh_data.refresh_token
    )

    current_user = await auth_service.get_current_user(db, token=tokens.access_token)

    await audit_log_service.log_event(
        db,
        action="refresh_token",
        entity="auth",
        actor=current_user,
        detail="Renovación de tokens exitosa."
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