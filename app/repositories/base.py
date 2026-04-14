from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=Any)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=Any)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        return await db.get(self.model, id)

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        skip = (page - 1) * limit

        base_query = select(self.model)
        conditions = []

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    if isinstance(value, (list, tuple)):
                        conditions.append(getattr(self.model, field).in_(value))
                    else:
                        conditions.append(getattr(self.model, field) == value)

        if search and search_fields:
            search_conditions = []
            pattern = f"%{search}%"

            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(
                        getattr(self.model, field).ilike(pattern)
                    )

            if search_conditions:
                conditions.append(or_(*search_conditions))

        if conditions:
            base_query = base_query.where(and_(*conditions))

        if hasattr(self.model, sort_by):
            order_fn = desc if order.lower() == "desc" else asc
            base_query = base_query.order_by(
                order_fn(getattr(self.model, sort_by))
            )

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        paged_query = base_query.offset(skip).limit(limit)
        result = await db.execute(paged_query)
        items = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": items
        }

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType
    ) -> ModelType:
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump()

        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        if hasattr(db_obj, "modified_at"):
            db_obj.modified_at = datetime.now(timezone.utc)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        db: AsyncSession,
        *,
        id: Any
    ) -> Optional[ModelType]:
        obj = await db.get(self.model, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def soft_remove(
        self,
        db: AsyncSession,
        *,
        id: Any,
        **kwargs
    ) -> Optional[ModelType]:
        obj = await db.get(self.model, id)
        if not obj:
            return None

        if hasattr(obj, "is_deleted"):
            obj.is_deleted = True
        if hasattr(obj, "deleted_at"):
            obj.deleted_at = datetime.now(timezone.utc)
        if hasattr(obj, "is_active"):
            obj.is_active = False

        for field, value in kwargs.items():
            if hasattr(obj, field):
                setattr(obj, field, value)

        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj