from typing import Any, Generic, Optional, TypeVar, List
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    codigo: int = Field(200, description="Código de estado interno")
    mensaje: str = Field("Operación exitosa", description="Mensaje informativo")
    resultado: Optional[T] = None

    model_config = ConfigDict(from_attributes=True)


class ApiResponseSimple(BaseModel):
    codigo: int = 200
    mensaje: str
    resultado: dict = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ApiError(BaseModel):
    codigo: int
    mensaje: str
    resultado: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class PagedResponse(BaseModel, Generic[T]):
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página actual")
    limit: int = Field(..., description="Registros por página")
    data: List[T] = Field(..., description="Lista de registros")

    model_config = ConfigDict(from_attributes=True)