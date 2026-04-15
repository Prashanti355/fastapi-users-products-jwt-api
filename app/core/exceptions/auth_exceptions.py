from app.core.exceptions.base import AppException


class AuthenticationException(AppException):
    def __init__(self, message: str = "Error de autenticación."):
        super().__init__(
            message=message,
            code=401
        )


class InvalidCredentialsException(AppException):
    def __init__(self, message: str = "Usuario o contraseña incorrectos."):
        super().__init__(
            message=message,
            code=401
        )


class InvalidTokenException(AppException):
    def __init__(self, message: str = "Token inválido o expirado."):
        super().__init__(
            message=message,
            code=401
        )


class ExpiredTokenException(AppException):
    def __init__(
        self,
        message: str = "El token ha expirado. Por favor, inicie sesión nuevamente.",
    ):
        super().__init__(
            message=message,
            code=401
        )


class InsufficientPermissionsException(AppException):
    def __init__(
        self,
        message: str = "No tiene permisos suficientes para realizar esta acción."
    ):
        super().__init__(
            message=message,
            code=403
        )


class InactiveUserException(AppException):
    def __init__(self, message: str = "La cuenta de usuario está desactivada."):
        super().__init__(
            message=message,
            code=403
        )


class UserInactiveException(InactiveUserException):
    pass


class UserNotFoundException(AppException):
    def __init__(self, message: str = "Usuario no encontrado."):
        super().__init__(
            message=message,
            code=404
        )


class TokenRefreshException(AppException):
    def __init__(
        self,
        message: str = "No se pudo refrescar el token."
    ):
        super().__init__(
            message=message,
            code=401
        )