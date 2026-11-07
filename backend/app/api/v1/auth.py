"""
Authentication API endpoints: Register, Login, Me.
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.models import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Dependency returning the current user if a valid token is provided, else None."""
    if not token:
        return None
    user_id = decode_access_token(token)
    if not user_id:
        return None
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Dependency requiring authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    stmt = select(User).where(User.email == payload.email)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"Registered new user: {user.email}")
    return user


@router.post("/login", response_model=Token)
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password and receive a JWT access token."""
    stmt = select(User).where(User.email == payload.email)
    user = (await db.execute(stmt)).scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.id, expires_delta=access_token_expires)

    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """Get profile information for the authenticated user."""
    return current_user
