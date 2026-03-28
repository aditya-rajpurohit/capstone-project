from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth_schemas import RegisterRequest, LoginRequest, AuthResponse
from app.api.utils.responses import success_response
from app.core.security import hash_password, verify_password, create_access_token
from app.database.metadata.models.user import UserModel
from app.database.metadata.session import get_async_session

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register")
# async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_db_session)):
async def register(payload: RegisterRequest):
    sessionmaker = get_async_session()

    async with sessionmaker() as session:
        stmt = select(UserModel).where(UserModel.email == payload.email)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = UserModel(
            email=payload.email,
            hashed_password=hash_password(payload.password),
        )

        session.add(user)
        await session.commit()

    return success_response(data={"message": "User registered successfully"})


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    sessionmaker = get_async_session()

    async with sessionmaker() as session:
        stmt = select(UserModel).where(UserModel.email == payload.email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(
            payload.password, user.hashed_password
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(subject=str(user.id))

    return AuthResponse(access_token=token)
