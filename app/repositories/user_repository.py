from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreateRequest, UserPartialUpdateRequest


class UserRepository(BaseRepository[User, UserCreateRequest, UserPartialUpdateRequest]):
    def __init__(self):
        super().__init__(User)

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        statement = select(User).where(User.username == username)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_users(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_deleted: bool = False
    ) -> Dict[str, Any]:
        filters = {"is_deleted": is_deleted}
        if is_active is not None:
            filters["is_active"] = is_active

        return await self.get_multi(
            db,
            page=page,
            limit=limit,
            sort_by=sort_by,
            order=order,
            filters=filters,
            search=search,
            search_fields=["username", "email", "first_name", "last_name"],
        )

    async def soft_delete(
        self, db: AsyncSession, *, user_id: Any, **kwargs
    ) -> Optional[User]:
        return await self.soft_remove(db, id=user_id, **kwargs)

    async def is_active(self, user: User) -> bool:
        return user.is_active

    async def is_superuser(self, user: User) -> bool:
        return user.is_superuser
