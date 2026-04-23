import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)


class PasswordResetTokenService:
    def __init__(
        self,
        repository: PasswordResetTokenRepository,
    ):
        self.repository = repository

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(48)

    async def create_token(
        self,
        db: AsyncSession,
        *,
        user_id,
        expires_in_minutes: int = 30,
    ) -> PasswordResetToken:
        token = self._generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=expires_in_minutes
        )

        return await self.repository.create(
            db,
            token=token,
            user_id=user_id,
            expires_at=expires_at,
        )

    async def get_valid_token(
        self,
        db: AsyncSession,
        *,
        token: str,
    ) -> PasswordResetToken | None:
        db_token = await self.repository.get_by_token(
            db,
            token=token,
        )

        if db_token is None:
            return None

        if db_token.used_at is not None:
            return None

        if db_token.expires_at < datetime.now(timezone.utc):
            return None

        return db_token

    async def mark_as_used(
        self,
        db: AsyncSession,
        *,
        password_reset_token: PasswordResetToken,
    ) -> PasswordResetToken:
        return await self.repository.mark_as_used(
            db,
            password_reset_token=password_reset_token,
        )
    
    async def get_latest_token_by_user_id(
        self,
        db: AsyncSession,
        *,
        user_id,
    ) -> PasswordResetToken | None:
        return await self.repository.get_latest_by_user_id(
            db,
            user_id=user_id,
        )    