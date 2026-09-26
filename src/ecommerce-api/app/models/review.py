import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from ..core.error_codes import *

class Review(Base):
    __tablename__ = "review"

    prod_id: Mapped[str] = mapped_column(String,ForeignKey("Product.prod_id"))
    review_id: Mapped[str] = mapped_column(String,primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String,ForeignKey("users.user_code"))
    review_comment: Mapped[str] = mapped_column(String(500))
    rating: Mapped[int] = mapped_column(Integer)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    process_id: Mapped[uuid.UUID] = mapped_column(primary_key=True,default=uuid.uuid4)