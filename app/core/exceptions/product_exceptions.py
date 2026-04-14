from typing import Optional
from uuid import UUID

from app.core.exceptions.base import AppException


class ProductNotFoundException(AppException):
    """
    Lanzada cuando un producto solicitado no existe
    por su ID.
    """
    def __init__(self, product_id: Optional[UUID] = None):
        self.product_id = product_id
        super().__init__(
            message="Producto no encontrado.",
            code=404
        )


class ProductAlreadyExistsException(AppException):
    """
    Lanzada cuando el nombre o la clave del producto
    ya están en uso.
    """
    def __init__(
        self,
        conflict_type: Optional[str] = None,
        value: Optional[str] = None
    ):
        if conflict_type == "name":
            message = f"El producto con nombre '{value}' ya existe."
        elif conflict_type == "product_key":
            message = f"La clave de producto '{value}' ya está en uso."
        else:
            message = "El producto ya existe."

        super().__init__(
            message=message,
            code=409
        )


class ProductNotDeletedException(AppException):
    """
    Lanzada al intentar restaurar un producto
    que no estaba eliminado.
    """
    def __init__(self):
        super().__init__(
            message="El producto no estaba eliminado.",
            code=400
        )


class ProductAlreadyDeletedException(AppException):
    """
    Lanzada al intentar eliminar lógicamente un producto
    que ya estaba eliminado.
    """
    def __init__(self):
        super().__init__(
            message="El producto ya estaba eliminado.",
            code=400
        )


class ProductAlreadyActiveException(AppException):
    """
    Lanzada al intentar activar un producto
    que ya estaba disponible.
    """
    def __init__(self):
        super().__init__(
            message="El producto ya estaba disponible.",
            code=400
        )


class ProductAlreadyInactiveException(AppException):
    """
    Lanzada al intentar desactivar un producto
    que ya estaba no disponible.
    """
    def __init__(self):
        super().__init__(
            message="El producto ya estaba no disponible.",
            code=400
        )


class InvalidProductPriceException(AppException):
    """
    Lanzada cuando el precio del producto
    es inválido.
    """
    def __init__(self):
        super().__init__(
            message="El precio del producto debe ser mayor a 0.",
            code=400
        )