import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer,Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from ..database import Base

class UserRole(str, enum.Enum):
    customer = "customer"
    seller = "seller"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True,default=uuid.uuid4)
    user_code: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.customer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())