from uuid import UUID

from app.core.exceptions.base import AppException


class CategoryNotFoundException(AppException):
    """
    Lanzada cuando una categoría solicitada no existe
    por su ID.
    """

    def __init__(self, category_id: UUID | None = None):
        self.category_id = category_id
        super().__init__(message="Categoría no encontrada.", code=404)


class CategoryAlreadyExistsException(AppException):
    """
    Lanzada cuando el nombre o el slug de la categoría
    ya están en uso.
    """

    def __init__(self, conflict_type: str | None = None, value: str | None = None):
        if conflict_type == "name":
            message = f"La categoría con nombre '{value}' ya existe."
        elif conflict_type == "slug":
            message = f"El slug de categoría '{value}' ya está en uso."
        else:
            message = "La categoría ya existe."

        super().__init__(message=message, code=409)


class CategoryNotDeletedException(AppException):
    """
    Lanzada al intentar restaurar una categoría
    que no estaba eliminada.
    """

    def __init__(self):
        super().__init__(message="La categoría no estaba eliminada.", code=400)


class CategoryAlreadyDeletedException(AppException):
    """
    Lanzada al intentar eliminar lógicamente una categoría
    que ya estaba eliminada.
    """

    def __init__(self):
        super().__init__(message="La categoría ya estaba eliminada.", code=400)


class CategoryAlreadyActiveException(AppException):
    """
    Lanzada al intentar activar una categoría
    que ya estaba activa.
    """

    def __init__(self):
        super().__init__(message="La categoría ya estaba activa.", code=400)


class CategoryAlreadyInactiveException(AppException):
    """
    Lanzada al intentar desactivar una categoría
    que ya estaba inactiva.
    """

    def __init__(self):
        super().__init__(message="La categoría ya estaba inactiva.", code=400)


class InvalidCategoryOperationException(AppException):
    """
    Lanzada cuando se intenta realizar una operación inválida
    sobre una categoría.
    """

    def __init__(self, message: str = "Operación inválida para la categoría."):
        super().__init__(message=message, code=400)
