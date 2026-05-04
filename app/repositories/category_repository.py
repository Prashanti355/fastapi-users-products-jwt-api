from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.category import Category
from app.repositories.base import BaseRepository
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryPartialUpdateRequest,
)


class CategoryRepository(
    BaseRepository[Category, CategoryCreateRequest, CategoryPartialUpdateRequest]
):
    def __init__(self):
        """
        Inicializa el repositorio de categorías
        reutilizando la lógica del BaseRepository.
        """
        super().__init__(Category)

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Category | None:
        """
        Busca una categoría por su nombre.
        Sirve para validar duplicados.
        """
        statement = select(Category).where(Category.name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, *, slug: str) -> Category | None:
        """
        Busca una categoría por su slug.
        Sirve para validar duplicados y consultas públicas.
        """
        statement = select(Category).where(Category.slug == slug)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_categories(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
        search: str | None = None,
        is_active: bool | None = None,
        is_deleted: bool = False,
    ) -> dict[str, Any]:
        """
        Lista paginada especializada para categorías,
        con filtros de estado, eliminación lógica y búsqueda.
        """
        filters: dict[str, Any] = {"is_deleted": is_deleted}

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
            search_fields=["name", "slug", "description"],
        )

    async def soft_delete(self, db: AsyncSession, *, category_id: Any, **kwargs) -> Category | None:
        """
        Wrapper de eliminación lógica específico
        para categorías.
        """
        return await self.soft_remove(db, id=category_id, **kwargs)
