from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.auth_exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenRefreshException,
)
from app.core.exceptions.user_exceptions import (
    UserAlreadyExistsException,
)
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.refresh_token_service import RefreshTokenService
from app.services.token_service import TokenService

from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    PublicRegisterRequest,
    TokenResponse,
)

from app.services.password_reset_token_service import PasswordResetTokenService


class AuthService:
    """
    Servicio de autenticación.
    Orquesta UserRepository y TokenService para implementar
    login, registro, refresh y usuario actual.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
        refresh_token_service=None,
        password_reset_token_service: PasswordResetTokenService | None = None,
    ):
        self.user_repo = user_repository
        self.token_service = token_service
        self.refresh_token_service = refresh_token_service
        self.password_reset_token_service = password_reset_token_service

    async def _store_refresh_token_if_enabled(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        refresh_token: str,
    ) -> None:
        """
        Persiste el refresh token emitido si el servicio de refresh tokens
        está disponible. No altera el flujo existente cuando no está inyectado.
        """
        if self.refresh_token_service is None:
            return

        token_data = self.token_service.verify_refresh_token(refresh_token)
        expires_at = datetime.fromtimestamp(token_data.exp, tz=timezone.utc)

        await self.refresh_token_service.register_token(
            db,
            jti=token_data.jti,
            user_id=user_id,
            expires_at=expires_at,
        )

    async def login(
        self,
        db: AsyncSession,
        *,
        login_data: LoginRequest
    ) -> TokenResponse:
        """
        Autentica al usuario con username + password
        y genera un nuevo par de tokens JWT.
        """
        user = await self.user_repo.get_by_username(
            db,
            username=login_data.username
        )

        if not user:
            raise InvalidCredentialsException()

        if not verify_password(login_data.password, user.password):
            raise InvalidCredentialsException()

        if not user.is_active or user.is_deleted:
            raise InactiveUserException()

        user.last_login = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        tokens = self.token_service.generate_tokens(user)

        await self._store_refresh_token_if_enabled(
            db,
            user_id=user.id,
            refresh_token=tokens.refresh_token,
        )

        return tokens

    async def register(
        self,
        db: AsyncSession,
        *,
        user_data: PublicRegisterRequest
    ) -> TokenResponse:
        """
        Registra un nuevo usuario y genera tokens JWT inmediatamente.
        """
        existing_user = await self.user_repo.get_by_username(
            db,
            username=user_data.username
        )
        if existing_user:
            raise UserAlreadyExistsException(
                conflict_type="username",
                value=user_data.username
            )

        if user_data.email:
            existing_email = await self.user_repo.get_by_email(
                db,
                email=user_data.email
            )
            if existing_email:
                raise UserAlreadyExistsException(
                    conflict_type="email",
                    value=user_data.email
                )

        user_dict = user_data.model_dump()
        user_dict["password"] = get_password_hash(user_data.password)
        user_dict["last_login"] = datetime.now(timezone.utc)

        # Endurecimiento de seguridad:
        # el registro público nunca debe crear superusuarios
        user_dict["is_superuser"] = False

        # El usuario registrado públicamente nace activo y no eliminado
        user_dict["is_active"] = True
        user_dict["is_deleted"] = False

        # El email no se considera verificado automáticamente
        user_dict["email_verified"] = False
        user_dict["email_verified_at"] = None

        # Normalizamos el rol a usuario estándar
        if not user_dict.get("role"):
            user_dict["role"] = "user"

        if user_dict.get("profile_picture") is not None:
            user_dict["profile_picture"] = str(user_dict["profile_picture"])

        db_user = User(**user_dict)

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        tokens = self.token_service.generate_tokens(db_user)

        await self._store_refresh_token_if_enabled(
            db,
            user_id=db_user.id,
            refresh_token=tokens.refresh_token,
        )

        return tokens

    async def refresh_token(
        self,
        db: AsyncSession,
        *,
        refresh_token: str
    ) -> TokenResponse:
        """
        Genera un nuevo par de tokens usando un refresh token válido.
        Si el servicio de refresh tokens está disponible, valida el token
        en base de datos, revoca el anterior por rotación y registra el nuevo.
        """
        token_data = self.token_service.verify_refresh_token(refresh_token)

        if self.refresh_token_service is not None:
            is_active = await self.refresh_token_service.is_token_active(
                db,
                jti=token_data.jti,
            )
            if not is_active:
                raise TokenRefreshException(
                    message="El refresh token fue revocado, expiró o no existe."
                )

        user = await self.user_repo.get(
            db,
            id=UUID(token_data.sub)
        )

        if not user:
            raise TokenRefreshException(
                message="El usuario asociado al token ya no existe."
            )

        if not user.is_active or user.is_deleted:
            raise InactiveUserException()

        if self.refresh_token_service is not None:
            await self.refresh_token_service.revoke_token(
                db,
                jti=token_data.jti,
                revoke_reason="rotated",
            )

        tokens = self.token_service.generate_tokens(user)

        await self._store_refresh_token_if_enabled(
            db,
            user_id=user.id,
            refresh_token=tokens.refresh_token,
        )

        return tokens

    async def get_current_user(
        self,
        db: AsyncSession,
        *,
        token: str
    ) -> CurrentUser:
        """
        Extrae y valida el usuario actual desde un access token.
        """
        token_data = self.token_service.verify_access_token(token)

        user = await self.user_repo.get(
            db,
            id=UUID(token_data.sub)
        )

        if not user:
            raise InvalidTokenException(
                message="El usuario asociado al token no existe."
            )

        if not user.is_active or user.is_deleted:
            raise InactiveUserException()

        return CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_superuser=user.is_superuser,
            is_active=user.is_active,
        )
    async def logout(
        self,
        db: AsyncSession,
        *,
        refresh_token: str
    ) -> None:
        """
        Revoca un refresh token válido. La operación es idempotente:
        si el token ya estaba revocado o no existe en la tabla, no falla.
        """
        token_data = self.token_service.verify_refresh_token(refresh_token)

        if self.refresh_token_service is None:
            return

        stored_token = await self.refresh_token_service.get_by_jti(
            db,
            jti=token_data.jti,
        )

        if stored_token is None:
            return

        if stored_token.revoked_at is not None:
            return

        await self.refresh_token_service.revoke_token(
            db,
            jti=token_data.jti,
            revoke_reason="logout",
        )    

    async def logout_all(
        self,
        db: AsyncSession,
        *,
        user_id: UUID
    ) -> int:
        """
        Revoca todos los refresh tokens activos del usuario.
        Retorna cuántos tokens fueron revocados.
        """
        if self.refresh_token_service is None:
            return 0

        revoked_tokens = await self.refresh_token_service.revoke_all_user_tokens(
            db,
            user_id=user_id,
            revoke_reason="logout_all",
        )

        return len(revoked_tokens)     


    async def forgot_password(
        self,
        db: AsyncSession,
        *,
        email: str,
    ) -> User | None:
        """
        Genera un token de recuperación si el usuario existe y está activo.
        La respuesta del endpoint debe seguir siendo neutra para no filtrar
        si el correo existe o no.
        """
        user = await self.user_repo.get_by_email(
            db,
            email=email,
        )

        if user is None:
            return None

        if not user.is_active or user.is_deleted:
            return None

        if self.password_reset_token_service is None:
            return None

        await self.password_reset_token_service.create_token(
            db,
            user_id=user.id,
            expires_in_minutes=30,
        )

        return user

    async def reset_password(
        self,
        db: AsyncSession,
        *,
        token: str,
        new_password: str,
    ) -> User:
        """
        Valida el token de recuperación, cambia la contraseña,
        marca el token como usado y revoca sesiones activas.
        """
        if self.password_reset_token_service is None:
            raise InvalidTokenException(
                message="El servicio de recuperación de contraseña no está disponible."
            )

        db_token = await self.password_reset_token_service.get_valid_token(
            db,
            token=token,
        )

        if db_token is None:
            raise InvalidTokenException(
                message="El token de recuperación es inválido o ha expirado."
            )

        user = await self.user_repo.get(
            db,
            id=db_token.user_id,
        )

        if user is None:
            raise InvalidTokenException(
                message="El usuario asociado al token no existe."
            )

        if not user.is_active or user.is_deleted:
            raise InactiveUserException()

        user.password = get_password_hash(new_password)

        db.add(user)
        await db.commit()
        await db.refresh(user)

        await self.password_reset_token_service.mark_as_used(
            db,
            password_reset_token=db_token,
        )

        if self.refresh_token_service is not None:
            await self.refresh_token_service.revoke_all_user_tokens(
                db,
                user_id=user.id,
                revoke_reason="password_reset",
            )

        return user       