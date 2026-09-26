from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..core.dependencies import require_role
from ..models.user import User, UserRole
from ..schemas.UserSchema import *
from sqlalchemy import select, update
from ..core.ExceptionHandler import *
from ..core.error_codes import *

router = APIRouter(prefix="/user",tags=["user"])

@router.get("/users",response_model=list[UserResponse],status_code=200)
async def list_users(current_user: User = Depends(require_role(UserRole.admin)),db:AsyncSession = Depends(get_db)) -> list[UserResponse]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.get("/users/{user_id}",response_model=UserResponse,status_code=200)
async def get_user(user_id: int,current_user: User = Depends(require_role(UserRole.admin)),db:AsyncSession = Depends(get_db)) -> UserResponse:
    user = await db.execute(select(User).where(User.user_code==user_id))
    user = user.scalar_one_or_none()
    if user is None:
        AppException(
            error_id=ErrorCode.USER_NOT_FOUND,
            message="User Not Found",
            severity="warning",
            category=Category.USER
        )
    return user

@router.patch("/users/{user_id}/role",response_model=UserResponse, status_code=200)
async def update_role(user_id: int,update_data: UpdateRoleAndStaus,current_user: User = Depends(require_role(UserRole.admin)),db: AsyncSession = Depends(get_db)) -> UserResponse:
    query = select(User).where(User.user_code==user_id)
    user_exisitance = await db.execute(query)
    if not user_exisitance.scalar_one_or_none():
        AppException(
            error_id=ErrorCode.USER_NOT_FOUND,
            message="User Not Found",
            severity="warning",
            category=Category.USER
        )
    data = update_data.model_dump(exclude_unset=True)

    result = await db.execute(
        update(User).where(User.user_code==user_id).values(**data)
    )
    if result.rowcount == 0:
        AppException(
            error_id=ErrorCode.UPDATE_FAILED,
            message="Updation Failed",
            severity="warning",
            category=Category.USER
        )

    await db.commit()
    user = await db.execute(select(User).where(User.user_code==user_id))
    return user.scalar_one()

@router.patch("/users/{user_id}/status",response_model=UserResponse, status_code=200)
async def update_status(user_id: int,update_data: UpdateRoleAndStaus,current_user: User = Depends(require_role(UserRole.admin)),db: AsyncSession = Depends(get_db)) -> UserResponse:
    query = select(User).where(User.user_code==user_id)
    user_exisitance = await db.execute(query)
    if not user_exisitance.scalar_one_or_none():
        AppException(
            error_id=ErrorCode.USER_NOT_FOUND,
            message="User Not Found",
            severity="warning",
            category=Category.USER
        )
    data = update_data.model_dump(exclude_unset=True)

    result = await db.execute(
        update(User).where(User.user_code==user_id).values(**data)
    )
    if result.rowcount == 0:
        AppException(
            error_id=ErrorCode.UPDATE_FAILED,
            message="Updation Failed",
            severity="warning",
            category=Category.USER
        )

    await db.commit()
    user = await db.execute(select(User).where(User.user_code==user_id))
    return user.scalar_one()