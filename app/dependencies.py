from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions.auth_exceptions import (
    InactiveUserException,
    InsufficientPermissionsException,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CurrentUser
from app.services.auth_service import AuthService
from app.services.product_service import ProductService
from app.services.token_service import TokenService
from app.services.user_service import UserService
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.audit_log_service import AuditLogService

# =========================================================
# OAuth2 / Swagger
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


# =========================================================
# Repositorios
# =========================================================

async def get_user_repository() -> UserRepository:
    return UserRepository()


async def get_product_repository() -> ProductRepository:
    return ProductRepository()


# =========================================================
# Servicios de dominio
# =========================================================

async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)


async def get_product_service(
    repository: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    return ProductService(repository)


# =========================================================
# Servicios de seguridad
# =========================================================

def get_token_service() -> TokenService:
    return TokenService()


async def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    token_service: TokenService = Depends(get_token_service),
) -> AuthService:
    return AuthService(user_repository, token_service)


# =========================================================
# Cadena de autenticación JWT
# =========================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    """
    Extrae y valida el usuario actual desde el access token JWT.
    """
    return await auth_service.get_current_user(db, token=token)


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Verifica que el usuario actual esté activo.
    """
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


async def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    """
    Verifica que el usuario actual sea superusuario.
    """
    if not current_user.is_superuser:
        raise InsufficientPermissionsException(
            message="Se requieren permisos de superusuario."
        )
    return current_user


# =========================================================
# Retrocompatibilidad / fallback temporal
# =========================================================

def get_current_user_id_flexible() -> UUID:
    """
    Fallback temporal para pruebas rápidas.
    Idealmente no debería usarse ya en endpoints protegidos.
    """
    return UUID("00000000-0000-0000-0000-000000000000")

async def get_audit_log_repository() -> AuditLogRepository:
    return AuditLogRepository()


async def get_audit_log_service(
    repository: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuditLogService:
    return AuditLogService(repository)