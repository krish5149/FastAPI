import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer,Enum as SAEnum, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from ..database import Base
from ..core.error_codes import *

class Product(Base):
    __tablename__ = "Product"

    prod_id: Mapped[str] = mapped_column(String,primary_key=True, index=True)
    user_code: Mapped[str] = mapped_column(String,ForeignKey("users.user_code"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    price: Mapped[str] = mapped_column(Integer)
    base_quantity: Mapped[int] = mapped_column(Integer,default=50)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())