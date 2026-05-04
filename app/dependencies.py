from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions.auth_exceptions import InsufficientPermissionsException
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CurrentUser
from app.services.audit_log_service import AuditLogService
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.email_service import EmailService
from app.services.password_reset_token_service import (
    PasswordResetTokenService,
)
from app.services.product_service import ProductService
from app.services.refresh_token_service import RefreshTokenService
from app.services.token_service import TokenService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_user_repository() -> UserRepository:
    return UserRepository()


async def get_product_repository() -> ProductRepository:
    return ProductRepository()


async def get_audit_log_repository() -> AuditLogRepository:
    return AuditLogRepository()


async def get_refresh_token_repository() -> RefreshTokenRepository:
    return RefreshTokenRepository()


def get_password_reset_token_repository() -> PasswordResetTokenRepository:
    return PasswordResetTokenRepository()


async def get_token_service() -> TokenService:
    return TokenService()


def get_email_service() -> EmailService:
    return EmailService()


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)


async def get_product_service(
    repository: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    return ProductService(repository)


async def get_category_repository() -> CategoryRepository:
    return CategoryRepository()


async def get_category_service(
    repository: CategoryRepository = Depends(get_category_repository),
) -> CategoryService:
    return CategoryService(repository)


async def get_audit_log_service(
    repository: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuditLogService:
    return AuditLogService(repository)


async def get_refresh_token_service(
    repository: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> RefreshTokenService:
    return RefreshTokenService(repository)


def get_password_reset_token_service(
    repository: PasswordResetTokenRepository = Depends(get_password_reset_token_repository),
) -> PasswordResetTokenService:
    return PasswordResetTokenService(repository)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    token_service: TokenService = Depends(get_token_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    password_reset_token_service: PasswordResetTokenService = Depends(
        get_password_reset_token_service
    ),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
        token_service=token_service,
        refresh_token_service=refresh_token_service,
        password_reset_token_service=password_reset_token_service,
        email_service=email_service,
    )


async def get_current_active_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    return await auth_service.get_current_user(db, token=token)


async def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    if not current_user.is_superuser:
        raise InsufficientPermissionsException(message="Se requieren privilegios de superusuario.")
    return current_user


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)
