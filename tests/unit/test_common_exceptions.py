from app.core.exceptions.common import (
    InternalServerException,
    InvalidPaginationException,
)


def test_invalid_pagination_exception_uses_default_values():
    exc = InvalidPaginationException()

    assert exc.message == "Parámetros de paginación inválidos."
    assert exc.code == 400


def test_invalid_pagination_exception_accepts_custom_message():
    exc = InvalidPaginationException("Página fuera de rango.")

    assert exc.message == "Página fuera de rango."
    assert exc.code == 400


def test_internal_server_exception_uses_default_values():
    exc = InternalServerException()

    assert exc.message == "Error interno del servidor."
    assert exc.code == 500


def test_internal_server_exception_accepts_custom_message():
    exc = InternalServerException("Fallo inesperado en el servicio.")

    assert exc.message == "Fallo inesperado en el servicio."
    assert exc.code == 500
