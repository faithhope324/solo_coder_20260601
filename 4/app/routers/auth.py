from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserOut, Token
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if auth_service.get_user_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if auth_service.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = auth_service.create_user(db, data.username, data.email, data.password)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(user.id, user.is_admin)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
