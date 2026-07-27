from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sqlalchemy import text

from app.api.deps import get_current_user
from app.core.security import create_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import AccessTokenOut, RefreshRequest, TokenPair, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/auth")


@router.get("/health")
def auth_health() -> dict:
    return {"status": "ok"}


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)) -> User:
    db.execute(text("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, full_name VARCHAR(255) NOT NULL, hashed_password VARCHAR(255), google_id VARCHAR(255), is_active BOOLEAN DEFAULT 1, is_verified BOOLEAN DEFAULT 0, created_at TIMESTAMP, updated_at TIMESTAMP)"))
    db.commit()
    existing_user = db.query(User).filter(User.email == str(payload.email)).first()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=str(payload.email),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> dict:
    db.execute(text("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, full_name VARCHAR(255) NOT NULL, hashed_password VARCHAR(255), google_id VARCHAR(255), is_active BOOLEAN DEFAULT 1, is_verified BOOLEAN DEFAULT 0, created_at TIMESTAMP, updated_at TIMESTAMP)"))
    db.commit()
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if user is None or user.hashed_password is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_token(str(user.id), "access")
    refresh_token = create_token(str(user.id), "refresh")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=AccessTokenOut)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    db.execute(text("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, full_name VARCHAR(255) NOT NULL, hashed_password VARCHAR(255), google_id VARCHAR(255), is_active BOOLEAN DEFAULT 1, is_verified BOOLEAN DEFAULT 0, created_at TIMESTAMP, updated_at TIMESTAMP)"))
    db.commit()
    from app.core.security import decode_token

    try:
        token_payload = decode_token(payload.refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return {"access_token": create_token(str(user.id), "access"), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user
