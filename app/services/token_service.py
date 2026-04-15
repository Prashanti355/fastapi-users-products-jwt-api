from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions.auth_exceptions import (
    InvalidTokenException,
    TokenRefreshException,
)
from app.schemas.auth import TokenResponse

class TokenPayload(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc
        
class TokenService:

    @staticmethod
    def _build_payload(
        *,
        user_id: str,
        username: str,
        role: str | None,
        is_superuser: bool,
        token_type: str,
        expires_delta: timedelta,
        include_jti: bool = False,
    ) -> tuple[dict, datetime]:
        now_utc = datetime.now(timezone.utc)
        expires_at = now_utc + expires_delta

        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "is_superuser": is_superuser,
            "token_type": token_type,
            "iat": int(now_utc.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        if include_jti:
            payload["jti"] = str(uuid4())

        return payload, expires_at

    @staticmethod
    def _encode_token(payload: dict) -> str:
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    @staticmethod
    def generate_access_token(user) -> str:
        payload, _ = TokenService._build_payload(
            user_id=str(user.id),
            username=user.username,
            role=getattr(user, "role", None),
            is_superuser=bool(getattr(user, "is_superuser", False)),
            token_type="access",
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            include_jti=False,
        )
        return TokenService._encode_token(payload)

    @staticmethod
    def generate_refresh_token(user) -> tuple[str, str, datetime]:
        payload, expires_at = TokenService._build_payload(
            user_id=str(user.id),
            username=user.username,
            role=getattr(user, "role", None),
            is_superuser=bool(getattr(user, "is_superuser", False)),
            token_type="refresh",
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            include_jti=True,
        )

        token = TokenService._encode_token(payload)
        return token, payload["jti"], expires_at
    
    @staticmethod
    def get_access_token_expires_in() -> int:
        return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


    @staticmethod
    def generate_tokens(user) -> TokenResponse:
        access_token = TokenService.generate_access_token(user)
        refresh_token, _, _ = TokenService.generate_refresh_token(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=TokenService.get_access_token_expires_in(),
        )

    @staticmethod
    def _decode_token(token: str) -> dict:
        try:
            return jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except JWTError as exc:
            raise InvalidTokenException(message="Token inválido o expirado.") from exc

    @staticmethod
    def verify_access_token(token: str):
        payload = TokenService._decode_token(token)

        if payload.get("token_type") != "access":
            raise InvalidTokenException(
                message="El token proporcionado no es un access token válido."
            )

        return TokenPayload(payload)

    @staticmethod
    def verify_refresh_token(token: str):
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except JWTError as exc:
            raise TokenRefreshException(
                message="Refresh token inválido o expirado."
            ) from exc

        if payload.get("token_type") != "refresh":
            raise TokenRefreshException(
                message="El token proporcionado no es un refresh token válido."
            )

        if not payload.get("jti"):
            raise TokenRefreshException(
                message="El refresh token no contiene un identificador válido."
            )

        return TokenPayload(payload)