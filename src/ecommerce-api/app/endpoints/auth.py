from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.user import User
from ..schemas.UserSchema import *
from ..core.security import hash_pwd, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from ..core.dependencies import get_current_user
from ..core.idgenerator import generate_unique_user_code
from sqlalchemy.future import select
from fastapi import HTTPException
from ..core.error_codes import *
from ..core.ExceptionHandler import *

router = APIRouter(prefix="/auth",tags=["auth"])

@router.post("/signup",response_model=UserCreateResponse,status_code=status.HTTP_201_CREATED)
async def signup(user_credential: UserCreate,db: AsyncSession = Depends(get_db)) -> UserCreateResponse:
    existing = await db.scalar(select(User).where(User.email==user_credential.email))
    if existing:
        raise AppException(
            error_id=ErrorCode.EMAIL_ALREADY_EXISTS,
            message="Email already existis try login",
            severity="warning",
            category=Category.AUTH,
            status_code=409
        )

    code = await generate_unique_user_code(db)
    user = User(
        user_code=code,
        email=user_credential.email,
        hashed_password=hash_pwd(user_credential.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user

@router.post("/login", response_model=Token, status_code=200)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise AppException(
            error_id=ErrorCode.INVALID_CREDENTIALS,
            message="User name or password incorect",
            severity="warning",
            category=Category.AUTH,
            status_code=409
        )

    token = create_access_token(user.id)
    return Token(access_token=token)

@router.get("/me", response_model=UserProfileResponse, status_code=200)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

