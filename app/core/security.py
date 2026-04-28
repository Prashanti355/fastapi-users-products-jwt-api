from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.auth import TokenData


def get_password_hash(password: str) -> str:
    """
    Convierte texto plano en un hash seguro usando bcrypt.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hash_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña coincide con el hash almacenado.
    """
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un access token JWT firmado.
    Incluye token_type='access' para diferenciarlo del refresh token.
    """
    to_encode = data.copy()
    to_encode["token_type"] = "access"

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un refresh token JWT firmado.
    Incluye token_type='refresh' para diferenciarlo del access token.
    """
    to_encode = data.copy()
    to_encode["token_type"] = "refresh"

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> TokenData | None:
    """
    Decodifica y valida un token JWT.

    Retorna TokenData si es válido.
    Retorna None si es inválido, expiró o el tipo no coincide.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        token_type: str = payload.get("token_type", "")
        if token_type != expected_type:
            return None

        sub: str | None = payload.get("sub")
        if sub is None:
            return None

        return TokenData(
            sub=sub,
            username=payload.get("username"),
            role=payload.get("role"),
            is_superuser=payload.get("is_superuser", False),
            token_type=token_type,
            exp=payload.get("exp"),
        )
    except JWTError:
        return None
