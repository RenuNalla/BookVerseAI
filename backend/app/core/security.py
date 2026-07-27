"""
Security primitives: password hashing and JWT issuing/verification.

Kept separate from services/auth_service.py: this file has ZERO knowledge
of the database or User model — it only knows about strings and tokens.
That separation makes it trivially unit-testable and reusable if we ever
add a second auth-consuming service.
"""

from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
TokenType = Literal["access", "refresh"]


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(subject: str, token_type: TokenType) -> str:
    """
    subject: usually the user's UUID as a string.
    token_type: "access" (short-lived, sent on every request) or
                "refresh" (long-lived, used only to mint new access tokens).
    """
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {"sub": subject, "type": token_type, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises jose.JWTError if the token is invalid, expired, or tampered with."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise exc
