import pytest

from app.core.exceptions.user_exceptions import (
    EmailAlreadyVerifiedException,
    EmailNotFoundException,
    EmailNotVerifiedException,
    InvalidCredentialsException,
    PasswordMismatchException,
    UserAlreadyActiveException,
    UserAlreadyExistsException,
    UserAlreadyInactiveException,
    UserNotDeletedException,
    UserNotFoundException,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_message", "expected_code"),
    [
        (UserNotFoundException, "Usuario no encontrado.", 404),
        (UserNotDeletedException, "El usuario no estaba eliminado.", 400),
        (EmailAlreadyVerifiedException, "El email ya estaba verificado.", 400),
        (UserAlreadyActiveException, "El usuario ya estaba activo.", 400),
        (UserAlreadyInactiveException, "El usuario ya estaba desactivado.", 400),
        (
            InvalidCredentialsException,
            "Datos inválidos o la contraseña actual no coincide.",
            401,
        ),
        (PasswordMismatchException, "Las nuevas contraseñas no coinciden.", 400),
        (EmailNotVerifiedException, "El email no ha sido verificado.", 400),
        (EmailNotFoundException, "No se encontró una cuenta con ese email.", 404),
    ],
)
def test_user_exceptions_use_expected_default_message_and_code(
    exc_cls,
    expected_message,
    expected_code,
):
    exc = exc_cls()

    assert exc.message == expected_message
    assert exc.code == expected_code


def test_user_already_exists_exception_uses_default_message():
    exc = UserAlreadyExistsException()

    assert exc.message == "El usuario ya existe."
    assert exc.code == 409


def test_user_already_exists_exception_formats_email_conflict_message():
    exc = UserAlreadyExistsException("email", "maya@example.com")

    assert exc.message == "El email maya@example.com ya está registrado."
    assert exc.code == 409


def test_user_already_exists_exception_formats_username_conflict_message():
    exc = UserAlreadyExistsException("username", "maya")

    assert exc.message == "El username maya ya está en uso."
    assert exc.code == 409
