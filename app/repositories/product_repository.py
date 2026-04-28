from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.product import Product
from app.repositories.base import BaseRepository
from app.schemas.product import (
    ProductCreateRequest,
    ProductPartialUpdateRequest,
)


class ProductRepository(BaseRepository[Product, ProductCreateRequest, ProductPartialUpdateRequest]):
    def __init__(self):
        """
        Inicializa el repositorio de productos
        reutilizando la lógica del BaseRepository.
        """
        super().__init__(Product)

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Product | None:
        """
        Busca un producto por su nombre.
        Sirve para validar duplicados.
        """
        statement = select(Product).where(Product.name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_product_key(self, db: AsyncSession, *, product_key: str) -> Product | None:
        """
        Busca un producto por su clave única.
        Sirve para validar duplicados.
        """
        statement = select(Product).where(Product.product_key == product_key)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_products(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
        search: str | None = None,
        status: bool | None = None,
        product_type: str | None = None,
        is_deleted: bool = False,
    ) -> dict[str, Any]:
        """
        Lista paginada especializada para productos,
        con filtros de disponibilidad, tipo y búsqueda.
        """
        filters: dict[str, Any] = {"is_deleted": is_deleted}

        if status is not None:
            filters["status"] = status

        if product_type is not None:
            filters["type"] = product_type

        return await self.get_multi(
            db,
            page=page,
            limit=limit,
            sort_by=sort_by,
            order=order,
            filters=filters,
            search=search,
            search_fields=["name", "description", "product_key"],
        )

    async def soft_delete(self, db: AsyncSession, *, product_id: Any, **kwargs) -> Product | None:
        """
        Wrapper de eliminación lógica específico
        para productos.
        """
        return await self.soft_remove(db, id=product_id, **kwargs)
