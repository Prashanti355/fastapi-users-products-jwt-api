from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        token: str,
        user_id,
        expires_at: datetime,
    ) -> PasswordResetToken:
        db_token = PasswordResetToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
        )
        db.add(db_token)
        await db.commit()
        await db.refresh(db_token)
        return db_token

    async def get_by_token(
        self,
        db: AsyncSession,
        *,
        token: str,
    ) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def mark_as_used(
        self,
        db: AsyncSession,
        *,
        password_reset_token: PasswordResetToken,
    ) -> PasswordResetToken:
        password_reset_token.used_at = datetime.now(UTC)
        db.add(password_reset_token)
        await db.commit()
        await db.refresh(password_reset_token)
        return password_reset_token

    async def get_latest_by_user_id(
        self,
        db: AsyncSession,
        *,
        user_id,
    ) -> PasswordResetToken | None:
        statement = (
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .order_by(PasswordResetToken.created_at.desc())
        )
        result = await db.execute(statement)
        return result.scalars().first()
