from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    """
    Campos comunes para operaciones de producto.
    """

    name: str = Field(..., max_length=255, description="Nombre del producto")
    type: str = Field(..., max_length=10, description="Tipo de producto")
    price: Decimal = Field(
        ..., gt=0, max_digits=8, decimal_places=2, description="Precio del producto"
    )
    status: bool = Field(default=True, description="Estado de disponibilidad")
    description: str | None = Field(default=None, description="Descripción detallada")
    product_key: str | None = Field(
        default=None, max_length=8, description="Clave única del producto"
    )
    image_link: str | None = Field(
        default=None, max_length=200, description="URL o ruta de la imagen"
    )

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El precio debe ser mayor a 0.")
        return v


class ProductRead(ProductBase):
    """
    Esquema completo de salida para respuestas detalladas.
    """

    id: UUID
    is_deleted: bool
    deleted_at: datetime | None = None
    created_at: datetime
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Alias de compatibilidad con la guía del PDF
Product = ProductRead


class ProductCreateRequest(ProductBase):
    """
    Esquema para la creación de nuevos productos.
    """

    pass


class ProductUpdateRequest(ProductBase):
    """
    Esquema para actualización completa (PUT).
    Hereda todos los campos requeridos.
    """

    pass


class ProductPartialUpdateRequest(BaseModel):
    """
    Esquema para actualización parcial (PATCH).
    Todos los campos son opcionales.
    """

    name: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default=None, max_length=10)
    price: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    status: bool | None = None
    description: str | None = None
    product_key: str | None = Field(default=None, max_length=8)
    image_link: str | None = Field(default=None, max_length=200)

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("El precio debe ser mayor a 0.")
        return v


class ProductBasic(BaseModel):
    """
    Esquema resumido para respuestas rápidas.
    """

    id: UUID
    name: str
    type: str
    price: Decimal
    status: bool
    product_key: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductDeleteResult(BaseModel):
    """
    Resultado de eliminación lógica o física.
    """

    id: UUID
    is_deleted: bool
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductRestoreResult(BaseModel):
    """
    Resultado de restauración de un producto eliminado.
    """

    id: UUID
    is_deleted: bool
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductToggleStatusResult(BaseModel):
    """
    Resultado de activar o desactivar disponibilidad.
    """

    id: UUID
    name: str
    status: bool

    model_config = ConfigDict(from_attributes=True)
