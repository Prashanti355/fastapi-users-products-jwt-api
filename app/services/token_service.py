from datetime import timedelta

from app.core.config import settings
from app.core.exceptions.auth_exceptions import (
    InvalidTokenException,
    TokenRefreshException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import TokenData, TokenResponse


class TokenService:
    """
    Servicio encargado de la generación y validación de tokens JWT.
    Encapsula toda la lógica de tokens para desacoplarla del servicio de auth.
    """

    @staticmethod
    def generate_tokens(user: User) -> TokenResponse:
        """
        Genera un par access_token + refresh_token para un usuario autenticado.
        """
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "is_superuser": user.is_superuser,
        }

        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )

        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def verify_access_token(token: str) -> TokenData:
        """
        Verifica un access token y retorna los datos decodificados.
        """
        token_data = verify_token(token, expected_type="access")
        if token_data is None:
            raise InvalidTokenException()
        return token_data

    @staticmethod
    def verify_refresh_token(token: str) -> TokenData:
        """
        Verifica un refresh token y retorna los datos decodificados.
        """
        token_data = verify_token(token, expected_type="refresh")
        if token_data is None:
            raise TokenRefreshException(
                message="El refresh token es inválido o ha expirado."
            )
        return token_data