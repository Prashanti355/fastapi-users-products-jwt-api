from app.core.exceptions.base import AppException


class AuthenticationException(AppException):
    """
    Error genérico de autenticación.
    """
    def __init__(self, message: str = "Error de autenticación."):
        super().__init__(
            message=message,
            code=401
        )


class InvalidCredentialsException(AppException):
    """
    Credenciales de inicio de sesión inválidas.
    """
    def __init__(self):
        super().__init__(
            message="Usuario o contraseña incorrectos.",
            code=401
        )


class InvalidTokenException(AppException):
    """
    Token JWT inválido, corrupto o expirado.
    """
    def __init__(self, message: str = "Token inválido o expirado."):
        super().__init__(
            message=message,
            code=401
        )


class ExpiredTokenException(AppException):
    """
    Token JWT expirado.
    """
    def __init__(self):
        super().__init__(
            message="El token ha expirado. Por favor, inicie sesión nuevamente.",
            code=401
        )


class InsufficientPermissionsException(AppException):
    """
    El usuario no tiene permisos suficientes.
    """
    def __init__(
        self,
        message: str = "No tiene permisos suficientes para realizar esta acción."
    ):
        super().__init__(
            message=message,
            code=403
        )


class InactiveUserException(AppException):
    """
    El usuario está desactivado o eliminado.
    """
    def __init__(self):
        super().__init__(
            message="La cuenta de usuario está desactivada.",
            code=403
        )


class TokenRefreshException(AppException):
    """
    Error al intentar refrescar el token.
    """
    def __init__(
        self,
        message: str = "No se pudo refrescar el token."
    ):
        super().__init__(
            message=message,
            code=401
        )