from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sanctuary_v2.backend.core.database import get_db
from sanctuary_v2.backend.models.user import User
from sanctuary_v2.backend.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from sanctuary_v2.backend.services.auth import hash_password, create_access_token, authenticate_user


router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db_session: AsyncSession = Depends(get_db)):
    result = await db_session.execute(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db_session: AsyncSession = Depends(get_db)):
    user = await authenticate_user(payload.username_or_email, payload.password, db_session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)
