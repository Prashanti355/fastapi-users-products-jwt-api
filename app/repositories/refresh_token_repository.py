from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: dict,
    ) -> RefreshToken:
        refresh_token = RefreshToken(**obj_in)
        db.add(refresh_token)
        await db.commit()
        await db.refresh(refresh_token)
        return refresh_token

    async def get_by_jti(
        self,
        db: AsyncSession,
        *,
        jti: str,
    ) -> Optional[RefreshToken]:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def revoke_by_jti(
        self,
        db: AsyncSession,
        *,
        jti: str,
        revoked_at: datetime,
        revoke_reason: str | None = None,
    ) -> Optional[RefreshToken]:
        token = await self.get_by_jti(db, jti=jti)
        if token is None:
            return None

        token.revoked_at = revoked_at
        token.revoke_reason = revoke_reason

        db.add(token)
        await db.commit()
        await db.refresh(token)
        return token

    async def revoke_all_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        revoked_at: datetime,
        revoke_reason: str | None = None,
    ) -> list[RefreshToken]:
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.revoked_at = revoked_at
            token.revoke_reason = revoke_reason
            db.add(token)

        await db.commit()

        for token in tokens:
            await db.refresh(token)

        return list(tokens)