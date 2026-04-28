from app.core.exceptions.base import AppException


class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(message="Usuario no encontrado.", code=404)


class UserAlreadyExistsException(AppException):
    def __init__(self, conflict_type: str | None = None, value: str | None = None):
        if conflict_type == "email":
            message = f"El email {value} ya está registrado."
        elif conflict_type == "username":
            message = f"El username {value} ya está en uso."
        else:
            message = "El usuario ya existe."
        super().__init__(message=message, code=409)


class UserNotDeletedException(AppException):
    def __init__(self):
        super().__init__(message="El usuario no estaba eliminado.", code=400)


class EmailAlreadyVerifiedException(AppException):
    def __init__(self):
        super().__init__(message="El email ya estaba verificado.", code=400)


class UserAlreadyActiveException(AppException):
    def __init__(self):
        super().__init__(message="El usuario ya estaba activo.", code=400)


class UserAlreadyInactiveException(AppException):
    def __init__(self):
        super().__init__(message="El usuario ya estaba desactivado.", code=400)


class InvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(
            message="Datos inválidos o la contraseña actual no coincide.", code=401
        )


class PasswordMismatchException(AppException):
    def __init__(self):
        super().__init__(message="Las nuevas contraseñas no coinciden.", code=400)


class EmailNotVerifiedException(AppException):
    def __init__(self):
        super().__init__(message="El email no ha sido verificado.", code=400)


class EmailNotFoundException(AppException):
    def __init__(self):
        super().__init__(message="No se encontró una cuenta con ese email.", code=404)
