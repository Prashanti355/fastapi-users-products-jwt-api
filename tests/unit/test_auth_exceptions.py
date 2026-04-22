import pytest

from app.core.exceptions.auth_exceptions import (
    AuthenticationException,
    ExpiredTokenException,
    InactiveUserException,
    InsufficientPermissionsException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenRefreshException,
    UserInactiveException,
    UserNotFoundException,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_message", "expected_code"),
    [
        (AuthenticationException, "Error de autenticación.", 401),
        (InvalidCredentialsException, "Usuario o contraseña incorrectos.", 401),
        (InvalidTokenException, "Token inválido o expirado.", 401),
        (
            ExpiredTokenException,
            "El token ha expirado. Por favor, inicie sesión nuevamente.",
            401,
        ),
        (
            InsufficientPermissionsException,
            "No tiene permisos suficientes para realizar esta acción.",
            403,
        ),
        (InactiveUserException, "La cuenta de usuario está desactivada.", 403),
        (UserNotFoundException, "Usuario no encontrado.", 404),
        (TokenRefreshException, "No se pudo refrescar el token.", 401),
    ],
)
def test_auth_exceptions_use_expected_default_message_and_code(
    exc_cls,
    expected_message,
    expected_code,
):
    exc = exc_cls()

    assert exc.message == expected_message
    assert exc.code == expected_code


def test_authentication_exception_accepts_custom_message():
    exc = AuthenticationException("Falló la autenticación personalizada.")

    assert exc.message == "Falló la autenticación personalizada."
    assert exc.code == 401


def test_insufficient_permissions_exception_accepts_custom_message():
    exc = InsufficientPermissionsException("Acceso denegado para esta operación.")

    assert exc.message == "Acceso denegado para esta operación."
    assert exc.code == 403


def test_user_inactive_exception_inherits_from_inactive_user_exception():
    exc = UserInactiveException()

    assert isinstance(exc, InactiveUserException)
    assert exc.message == "La cuenta de usuario está desactivada."
    assert exc.code == 403