from uuid import UUID

from fastapi import APIRouter, Body, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession


from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.dependencies import (
    get_audit_log_service,
    get_auth_service,
    get_current_active_user,
    get_request_id,
    get_token_service,
    get_user_repository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    PublicRegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.response import ApiResponse, ApiResponseSimple
from app.services.audit_log_service import AuditLogService
from app.services.auth_service import AuthService
from app.services.token_service import TokenService


router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Autentica al usuario y devuelve un access token y un refresh token."
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    request_id: str | None = Depends(get_request_id),
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
        request_id=request_id,
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
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    response: Response,
    user_data: PublicRegisterRequest = Body(
        ...,
        description="Datos públicos del nuevo usuario"
    ),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    request_id: str | None = Depends(get_request_id),
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
        request_id=request_id,
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
    request_id: str | None = Depends(get_request_id),
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
        request_id=request_id,
        detail="Renovación de tokens exitosa."
    )

    return ApiResponse[TokenResponse](
        codigo=200,
        mensaje="Tokens renovados correctamente.",
        resultado=tokens
    )


@router.post(
    "/forgot-password",
    response_model=ApiResponseSimple,
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperación de contraseña",
    description=(
        "Si el correo existe, genera un token de recuperación. "
        "La respuesta es neutra para no exponer si el correo está registrado."
    ),
)
async def forgot_password(
    forgot_data: ForgotPasswordRequest = Body(
        ...,
        description="Correo del usuario",
    ),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    request_id: str | None = Depends(get_request_id),
):
    user = await auth_service.forgot_password(
        db,
        email=forgot_data.email,
    )

    if user is not None:
        actor = CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_superuser=user.is_superuser,
            is_active=user.is_active,
        )

        await audit_log_service.log_event(
            db,
            action="forgot_password",
            entity="auth",
            actor=actor,
            request_id=request_id,
            detail="Solicitud de recuperación de contraseña generada.",
        )

    return ApiResponseSimple(
        codigo=200,
        mensaje="Si el correo existe, se generó un enlace de recuperación.",
        resultado={},
    )


@router.post(
    "/reset-password",
    response_model=ApiResponseSimple,
    status_code=status.HTTP_200_OK,
    summary="Restablecer contraseña",
    description="Valida el token de recuperación y actualiza la contraseña.",
)
async def reset_password(
    reset_data: ResetPasswordRequest = Body(
        ...,
        description="Token de recuperación y nueva contraseña",
    ),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    request_id: str | None = Depends(get_request_id),
):
    user = await auth_service.reset_password(
        db,
        token=reset_data.token,
        new_password=reset_data.new_password,
    )

    actor = CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_superuser=user.is_superuser,
        is_active=user.is_active,
    )

    await audit_log_service.log_event(
        db,
        action="reset_password",
        entity="auth",
        actor=actor,
        request_id=request_id,
        detail="Restablecimiento de contraseña exitoso.",
    )

    return ApiResponseSimple(
        codigo=200,
        mensaje="Contraseña restablecida correctamente.",
        resultado={},
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


@router.post(
    "/logout",
    response_model=ApiResponseSimple,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión",
    description="Revoca el refresh token proporcionado por el cliente.",
)
async def logout(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service),
    user_repository: UserRepository = Depends(get_user_repository),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    request_id: str | None = Depends(get_request_id),
):
    token_data = token_service.verify_refresh_token(refresh_data.refresh_token)

    user = await user_repository.get(
        db,
        id=UUID(token_data.sub),
    )

    await auth_service.logout(
        db,
        refresh_token=refresh_data.refresh_token,
    )

    if user is not None:
        current_user = CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_superuser=user.is_superuser,
            is_active=user.is_active,
        )

        await audit_log_service.log_event(
            db,
            action="logout",
            entity="auth",
            actor=current_user,
            request_id=request_id,
            detail="Cierre de sesión exitoso."
        )

    return ApiResponseSimple(
        codigo=200,
        mensaje="Sesión cerrada exitosamente.",
        resultado={},
    )


@router.post(
    "/logout-all",
    response_model=ApiResponseSimple,
    status_code=status.HTTP_200_OK,
    summary="Cerrar todas las sesiones",
    description="Revoca todos los refresh tokens activos del usuario autenticado.",
)
async def logout_all(
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    request_id: str | None = Depends(get_request_id),
):
    revoked_count = await auth_service.logout_all(
        db,
        user_id=current_user.id,
    )

    await audit_log_service.log_event(
        db,
        action="logout_all",
        entity="auth",
        actor=current_user,
        request_id=request_id,
        detail=f"Cierre de todas las sesiones exitoso. Tokens revocados: {revoked_count}."
    )

    return ApiResponseSimple(
        codigo=200,
        mensaje="Todas las sesiones fueron cerradas exitosamente.",
        resultado={"revoked_tokens": revoked_count},
    )