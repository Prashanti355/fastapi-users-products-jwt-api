from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    """
    Campos comunes para operaciones de categoría.
    """

    name: str = Field(..., min_length=2, max_length=100, description="Nombre de la categoría")
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
        description="Identificador URL de la categoría",
    )
    description: str | None = Field(default=None, description="Descripción de la categoría")
    is_active: bool = Field(default=True, description="Estado activo de la categoría")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned_value = value.strip()

        if len(cleaned_value) < 2:
            raise ValueError("El nombre de la categoría debe tener al menos 2 caracteres.")

        return cleaned_value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value

        cleaned_value = value.strip()

        if len(cleaned_value) < 2:
            raise ValueError("El slug de la categoría debe tener al menos 2 caracteres.")

        return cleaned_value


class CategoryRead(CategoryBase):
    """
    Esquema completo de salida para respuestas detalladas.
    """

    id: UUID
    is_deleted: bool
    deleted_at: datetime | None = None
    created_at: datetime
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Alias de compatibilidad con el estilo usado en otros módulos
Category = CategoryRead


class CategoryCreateRequest(CategoryBase):
    """
    Esquema para la creación de nuevas categorías.
    """

    pass


class CategoryUpdateRequest(CategoryBase):
    """
    Esquema para actualización completa (PUT).
    Hereda todos los campos requeridos.
    """

    pass


class CategoryPartialUpdateRequest(BaseModel):
    """
    Esquema para actualización parcial (PATCH).
    Todos los campos son opcionales.
    """

    name: str | None = Field(default=None, min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value

        cleaned_value = value.strip()

        if len(cleaned_value) < 2:
            raise ValueError("El nombre de la categoría debe tener al menos 2 caracteres.")

        return cleaned_value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is None:
            return value

        cleaned_value = value.strip()

        if len(cleaned_value) < 2:
            raise ValueError("El slug de la categoría debe tener al menos 2 caracteres.")

        return cleaned_value


class CategoryBasic(BaseModel):
    """
    Esquema resumido para respuestas rápidas.
    """

    id: UUID
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryDeleteResult(BaseModel):
    """
    Resultado de eliminación lógica.
    """

    id: UUID
    is_deleted: bool
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CategoryRestoreResult(BaseModel):
    """
    Resultado de restauración de una categoría eliminada.
    """

    id: UUID
    is_deleted: bool
    deleted_at: datetime | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryToggleStatusResult(BaseModel):
    """
    Resultado de activar o desactivar una categoría.
    """

    id: UUID
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
