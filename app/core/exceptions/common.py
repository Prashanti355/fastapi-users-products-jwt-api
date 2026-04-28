from app.core.exceptions.base import AppException


class InvalidPaginationException(AppException):
    """
    Excepción lanzada cuando los parámetros de paginación
    (page, limit) son inválidos.
    """

    def __init__(self, message: str = "Parámetros de paginación inválidos."):
        super().__init__(message=message, code=400)


class InternalServerException(AppException):
    """
    Excepción genérica para errores no controlados
    del servidor.
    """

    def __init__(self, message: str = "Error interno del servidor."):
        super().__init__(message=message, code=500)
