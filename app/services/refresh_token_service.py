from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import RefreshTokenRepository


class RefreshTokenService:
    def __init__(self, repository: RefreshTokenRepository):
        self.repository = repository

    async def register_token(
        self,
        db: AsyncSession,
        *,
        jti: str,
        user_id: UUID,
        expires_at: datetime,
    ) -> RefreshToken:
        return await self.repository.create(
            db,
            obj_in={
                "jti": jti,
                "user_id": user_id,
                "token_type": "refresh",
                "expires_at": expires_at,
            },
        )

    async def get_by_jti(
        self,
        db: AsyncSession,
        *,
        jti: str,
    ) -> RefreshToken | None:
        return await self.repository.get_by_jti(db, jti=jti)

    async def is_token_active(
        self,
        db: AsyncSession,
        *,
        jti: str,
    ) -> bool:
        token = await self.repository.get_by_jti(db, jti=jti)

        if token is None:
            return False

        if token.revoked_at is not None:
            return False

        now_utc = datetime.now(timezone.utc)

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now_utc:
            return False

        return True

    async def revoke_token(
        self,
        db: AsyncSession,
        *,
        jti: str,
        revoke_reason: str | None = None,
    ) -> RefreshToken | None:
        return await self.repository.revoke_by_jti(
            db,
            jti=jti,
            revoked_at=datetime.now(timezone.utc),
            revoke_reason=revoke_reason,
        )

    async def revoke_all_user_tokens(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        revoke_reason: str | None = None,
    ) -> list[RefreshToken]:
        return await self.repository.revoke_all_for_user(
            db,
            user_id=user_id,
            revoked_at=datetime.now(timezone.utc),
            revoke_reason=revoke_reason,
        )