from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, hash_password, verify_password, create_access_token
from app.database import get_db
from app.models import User as UserModel
from app.schemas import UserRegister, UserLogin, Token, ApiResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserModel).where(UserModel.username == body.username)
    )
    if result.scalar_one_or_none():
        return ApiResponse(code=1, message="用户名已存在")
    user = UserModel(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return ApiResponse(code=0, data={"id": user.id, "username": user.username}, message="注册成功")


@router.post("/login")
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserModel).where(UserModel.username == body.username)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        return ApiResponse(code=1, message="用户名或密码错误")
    token = create_access_token(user.id, user.username)
    return ApiResponse(code=0, data={"access_token": token, "token_type": "bearer"}, message="登录成功")
