from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.user_exceptions import (
    InvalidCredentialsException,
    PasswordMismatchException,
    UserAlreadyActiveException,
    UserAlreadyExistsException,
    UserAlreadyInactiveException,
    UserNotDeletedException,
    UserNotFoundException,
)
from app.core.exceptions.auth_exceptions import InsufficientPermissionsException
from app.schemas.auth import CurrentUser
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    PasswordChangeRequest,
    UserCreateRequest,
    UserPartialUpdateRequest,
    UserUpdateRequest,
)


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def _ensure_no_privileged_self_update(
        self,
        *,
        db_obj: User,
        update_data: dict,
        current_user: CurrentUser | None
    ) -> None:
        """
        Evita que un usuario no superusuario modifique campos administrativos
        en su propia cuenta o en otra cuenta.
        """
        if current_user is None:
            return

        if current_user.is_superuser:
            return

        privileged_fields = (
            "is_active",
            "is_superuser",
            "role",
        )

        attempted_changes = [
            field
            for field in privileged_fields
            if field in update_data and update_data[field] != getattr(db_obj, field)
        ]

        if attempted_changes:
            raise InsufficientPermissionsException(
                message=(
                    "No tiene permisos para modificar campos administrativos: "
                    + ", ".join(attempted_changes)
                )
            )
    async def get_user_by_id(
        self,
        db: AsyncSession,
        *,
        user_id: Any
    ) -> User:
        db_obj = await self.user_repo.get(db, user_id)
        if not db_obj:
            raise UserNotFoundException()
        return db_obj

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
    ) -> dict:
        result = await self.user_repo.get_multi_users(
            db,
            page=page,
            limit=limit,
            sort_by=sort_by,
            order=order,
            search=search,
            is_active=is_active,
            is_deleted=is_deleted
        )
        return {
            "total": result["total"],
            "page": result["page"],
            "limit": result["limit"],
            "data": result["items"]
        }

    async def create_user(
        self,
        db: AsyncSession,
        *,
        user_in: UserCreateRequest
    ) -> User:
        if user_in.email:
            email_user = await self.user_repo.get_by_email(db, email=user_in.email)
            if email_user:
                raise UserAlreadyExistsException("email", user_in.email)

        username_user = await self.user_repo.get_by_username(
            db,
            username=user_in.username
        )
        if username_user:
            raise UserAlreadyExistsException("username", user_in.username)

        user_data = user_in.model_dump()
        user_data["password"] = get_password_hash(user_in.password)

        return await self.user_repo.create(db, obj_in=user_data)

    async def update_user(
        self,
        db: AsyncSession,
        *,
        user_id: Any,
        user_in: UserUpdateRequest,
        current_user: CurrentUser | None = None
    ) -> User:
        db_obj = await self.get_user_by_id(db, user_id=user_id)

        # Check for privileged field modifications
        self._ensure_no_privileged_self_update(
            db_obj=db_obj,
            update_data=user_in.model_dump(),
            current_user=current_user
        )

        if user_in.email and user_in.email != db_obj.email:
            email_user = await self.user_repo.get_by_email(db, email=user_in.email)
            if email_user:
                raise UserAlreadyExistsException("email", user_in.email)

        if user_in.username != db_obj.username:
            username_user = await self.user_repo.get_by_username(
                db,
                username=user_in.username
            )
            if username_user:
                raise UserAlreadyExistsException("username", user_in.username)

        update_data = user_in.model_dump()

        self._ensure_no_privileged_self_update(
            db_obj=db_obj,
            update_data=update_data,
            current_user=current_user
        )

        update_data["password"] = get_password_hash(user_in.password)
        return await self.user_repo.update(
            db,
            db_obj=db_obj,
            obj_in=update_data
        )

    async def partial_update_user(
        self,
        db: AsyncSession,
        *,
        user_id: Any,
        user_in: UserPartialUpdateRequest,
        current_user: CurrentUser | None = None
    ) -> User:
        db_obj = await self.get_user_by_id(db, user_id=user_id)

        if user_in.email and user_in.email != db_obj.email:
            email_user = await self.user_repo.get_by_email(db, email=user_in.email)
            if email_user:
                raise UserAlreadyExistsException("email", user_in.email)

        if user_in.username and user_in.username != db_obj.username:
            username_user = await self.user_repo.get_by_username(
                db,
                username=user_in.username
            )
            if username_user:
                raise UserAlreadyExistsException("username", user_in.username)

        update_data = user_in.model_dump(exclude_unset=True)

        self._ensure_no_privileged_self_update(
            db_obj=db_obj,
            update_data=update_data,
            current_user=current_user
        )

        if "password" in update_data and update_data["password"]:
            update_data["password"] = get_password_hash(update_data["password"])

        return await self.user_repo.update(
            db,
            db_obj=db_obj,
            obj_in=update_data
        )

    async def change_password(
        self,
        db: AsyncSession,
        *,
        user_id: Any,
        password_data: PasswordChangeRequest
    ) -> User:
        db_obj = await self.get_user_by_id(db, user_id=user_id)

        if not verify_password(password_data.current_password, db_obj.password):
            raise InvalidCredentialsException()

        if password_data.new_password != password_data.confirm_password:
            raise PasswordMismatchException()

        return await self.user_repo.update(
            db,
            db_obj=db_obj,
            obj_in={"password": get_password_hash(password_data.new_password)}
        )

    async def delete_user(
        self,
        db: AsyncSession,
        *,
        user_id: Any,
        deleted_by: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> User:
        await self.get_user_by_id(db, user_id=user_id)

        deleted_user = await self.user_repo.soft_delete(
            db,
            user_id=user_id,
            deleted_by=deleted_by,
            deactivation_reason=reason
        )

        return deleted_user

    async def restore_user(
        self,
        db: AsyncSession,
        *,
        user_id: Any
    ) -> User:
        db_obj = await self.get_user_by_id(db, user_id=user_id)

        if not db_obj.is_deleted:
            raise UserNotDeletedException()

        return await self.user_repo.update(
            db,
            db_obj=db_obj,
            obj_in={
                "is_deleted": False,
                "deleted_at": None,
                "deleted_by": None,
                "deactivation_reason": None,
                "is_active": True
            }
        )

    async def activate_user(
        self,
        db: AsyncSession,
        *,
        user_id: Any
    ) -> User:
        db_obj = await self.get_user_by_id(db, user_id=user_id)

        if db_obj.is_active:
            raise UserAlreadyActiveException()

        return await self.user_repo.update(
            db,
            db_obj=db_obj,
            obj_in={
                "is_active": True,
                "deactivation_reason": None
            }
        )

    async def deactivate_user(
        self,
        db: AsyncSession,
        *,
        user_id: Any,
        reason: Optional[str] = None
    ) -> User:
        db_obj = await self.get_user_by_id(db, user_id=user_id)

        if not db_obj.is_active:
            raise UserAlreadyInactiveException()

        return await self.user_repo.update(
            db,
            db_obj=db_obj,
            obj_in={
                "is_active": False,
                "deactivation_reason": reason
            }
        )