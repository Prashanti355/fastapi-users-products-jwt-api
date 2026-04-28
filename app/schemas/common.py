from enum import Enum
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=100, description="Elementos por página")


class SortingParams(BaseModel):
    sort_by: str = Field("created_at", description="Campo por el cual ordenar")
    order: SortOrder = Field(SortOrder.DESC, description="Dirección del ordenamiento")


class SearchParams(BaseModel):
    search: Optional[str] = Field(None, description="Texto de búsqueda general")
    is_active: Optional[bool] = Field(
        None, description="Filtrar por estado activo/inactivo"
    )


class PagedResult(BaseModel, Generic[T]):
    total: int
    page: int
    limit: int
    data: List[T]

    model_config = ConfigDict(from_attributes=True)
