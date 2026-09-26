import uuid
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from ..models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserCreateResponse(BaseModel):
    id: uuid.UUID
    user_code: int
    email: EmailStr
    role: UserRole
    is_active: bool

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class Token(BaseModel):
    token_type: str = "bearer"
    access_token: str

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_code: int
    email: EmailStr
    role: UserRole
    is_active: bool

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_code: int
    email: EmailStr
    role: UserRole
    created_at: datetime
    is_active: bool

class UpdateRoleAndStaus(BaseModel):
    role: UserRole |None = None
    is_active: bool | None = None