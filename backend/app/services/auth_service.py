"""
All auth business logic lives here, not in the endpoint functions.
Endpoints stay thin: parse request -> call service -> return response.
This is what makes the logic reusable (e.g. from a CLI seed script or
a Celery task) and unit-testable without spinning up FastAPI.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserRegister


class AuthError(Exception):
    """Raised for any auth failure the endpoint should turn into a 4xx."""


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def register_user(db: Session, data: UserRegister) -> User:
    if get_user_by_email(db, data.email):
        raise AuthError("An account with this email already exists.")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password:
        raise AuthError("Invalid email or password.")
    if not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password.")
    if not user.is_active:
        raise AuthError("This account has been deactivated.")
    return user