import re
import unicodedata
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.category_exceptions import (
    CategoryAlreadyActiveException,
    CategoryAlreadyDeletedException,
    CategoryAlreadyExistsException,
    CategoryAlreadyInactiveException,
    CategoryNotDeletedException,
    CategoryNotFoundException,
    InvalidCategoryOperationException,
)
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryPartialUpdateRequest,
    CategoryUpdateRequest,
)


def normalize_category_slug(value: str) -> str:
    """
    Normaliza un texto para usarlo como slug.
    """
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower().strip()
    dashed = re.sub(r"[^a-z0-9]+", "-", lowered)
    cleaned = dashed.strip("-")
    return cleaned


class CategoryService:
    def __init__(self, category_repository: CategoryRepository):
        """
        Inicializa el servicio de categorías con su
        repositorio correspondiente.
        """
        self.category_repo = category_repository

    async def create_category(self, db: AsyncSession, *, obj_in: CategoryCreateRequest) -> Category:
        """
        Registra una nueva categoría validando duplicidad
        de nombre y slug.
        """
        slug = normalize_category_slug(obj_in.slug or obj_in.name)

        if not slug:
            raise InvalidCategoryOperationException(
                message="El slug de la categoría no puede quedar vacío."
            )

        category_exists = await self.category_repo.get_by_name(db, name=obj_in.name)
        if category_exists:
            raise CategoryAlreadyExistsException(conflict_type="name", value=obj_in.name)

        slug_exists = await self.category_repo.get_by_slug(db, slug=slug)
        if slug_exists:
            raise CategoryAlreadyExistsException(conflict_type="slug", value=slug)

        create_data = obj_in.model_dump()
        create_data["slug"] = slug

        return await self.category_repo.create(db, obj_in=create_data)

    async def get_category_by_id(
        self, db: AsyncSession, *, category_id: Any, include_deleted: bool = False
    ) -> Category:
        """
        Retorna una categoría por su ID o lanza 404
        si no existe.
        """
        category = await self.category_repo.get(db, id=category_id)

        if not category:
            raise CategoryNotFoundException(category_id=category_id)

        if not include_deleted and category.is_deleted:
            raise CategoryNotFoundException(category_id=category_id)

        return category

    async def get_public_category_by_id(self, db: AsyncSession, *, category_id: Any) -> Category:
        """
        Retorna una categoría pública activa y no eliminada.
        """
        category = await self.get_category_by_id(
            db,
            category_id=category_id,
            include_deleted=False,
        )

        if not category.is_active:
            raise CategoryNotFoundException(category_id=category_id)

        return category

    async def get_multi_categories(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
        search: str | None = None,
        is_active: bool | None = True,
        is_deleted: bool = False,
    ) -> dict[str, Any]:
        """
        Obtiene una lista paginada de categorías
        con filtros de búsqueda y estado.
        """
        return await self.category_repo.get_multi_categories(
            db,
            page=page,
            limit=limit,
            sort_by=sort_by,
            order=order,
            search=search,
            is_active=is_active,
            is_deleted=is_deleted,
        )

    async def update_category(
        self,
        db: AsyncSession,
        *,
        category_id: Any,
        obj_in: CategoryUpdateRequest | CategoryPartialUpdateRequest,
    ) -> Category:
        """
        Actualiza la información de una categoría existente.
        Acepta tanto actualización completa (PUT)
        como parcial (PATCH).
        """
        db_obj = await self.get_category_by_id(
            db,
            category_id=category_id,
            include_deleted=True,
        )

        update_data = obj_in.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != db_obj.name:
            existing = await self.category_repo.get_by_name(db, name=update_data["name"])
            if existing:
                raise CategoryAlreadyExistsException(
                    conflict_type="name", value=update_data["name"]
                )

        if "slug" in update_data:
            requested_slug = update_data["slug"]

            if requested_slug:
                normalized_slug = normalize_category_slug(requested_slug)
            elif "name" in update_data:
                normalized_slug = normalize_category_slug(update_data["name"])
            else:
                normalized_slug = db_obj.slug

            if not normalized_slug:
                raise InvalidCategoryOperationException(
                    message="El slug de la categoría no puede quedar vacío."
                )

            if normalized_slug != db_obj.slug:
                existing = await self.category_repo.get_by_slug(db, slug=normalized_slug)
                if existing:
                    raise CategoryAlreadyExistsException(
                        conflict_type="slug", value=normalized_slug
                    )

            update_data["slug"] = normalized_slug
        elif "name" in update_data and update_data["name"] != db_obj.name:
            normalized_slug = normalize_category_slug(update_data["name"])

            if not normalized_slug:
                raise InvalidCategoryOperationException(
                    message="El slug de la categoría no puede quedar vacío."
                )

            if normalized_slug != db_obj.slug:
                existing = await self.category_repo.get_by_slug(db, slug=normalized_slug)
                if existing:
                    raise CategoryAlreadyExistsException(
                        conflict_type="slug", value=normalized_slug
                    )

            update_data["slug"] = normalized_slug

        return await self.category_repo.update(db, db_obj=db_obj, obj_in=update_data)

    async def delete_category(self, db: AsyncSession, *, category_id: Any) -> Category:
        """
        Elimina lógicamente una categoría.
        """
        db_obj = await self.get_category_by_id(
            db,
            category_id=category_id,
            include_deleted=True,
        )

        if db_obj.is_deleted:
            raise CategoryAlreadyDeletedException()

        return await self.category_repo.soft_delete(db, category_id=category_id)

    async def restore_category(self, db: AsyncSession, *, category_id: Any) -> Category:
        """
        Restaura una categoría eliminada lógicamente.
        """
        db_obj = await self.get_category_by_id(
            db,
            category_id=category_id,
            include_deleted=True,
        )

        if not db_obj.is_deleted:
            raise CategoryNotDeletedException()

        existing_slug = await self.category_repo.get_by_slug(db, slug=db_obj.slug)
        if existing_slug and existing_slug.id != db_obj.id:
            raise CategoryAlreadyExistsException(conflict_type="slug", value=db_obj.slug)

        update_data = {
            "is_deleted": False,
            "is_active": True,
            "deleted_at": None,
        }

        return await self.category_repo.update(db, db_obj=db_obj, obj_in=update_data)

    async def activate_category(self, db: AsyncSession, *, category_id: Any) -> Category:
        """
        Activa una categoría inactiva.
        """
        db_obj = await self.get_category_by_id(
            db,
            category_id=category_id,
            include_deleted=True,
        )

        if db_obj.is_deleted:
            raise InvalidCategoryOperationException(
                message="No se puede activar una categoría eliminada. Debe restaurarse primero."
            )

        if db_obj.is_active:
            raise CategoryAlreadyActiveException()

        return await self.category_repo.update(db, db_obj=db_obj, obj_in={"is_active": True})

    async def deactivate_category(self, db: AsyncSession, *, category_id: Any) -> Category:
        """
        Desactiva una categoría sin eliminarla.
        """
        db_obj = await self.get_category_by_id(db, category_id=category_id)

        if not db_obj.is_active:
            raise CategoryAlreadyInactiveException()

        return await self.category_repo.update(db, db_obj=db_obj, obj_in={"is_active": False})
