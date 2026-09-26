import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Order(Base):
    __tablename__ = "order"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_code"))
    order_id: Mapped[str] = mapped_column(String,primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String)
    total: Mapped[float] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    process_id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4)

    items: Mapped[list["OrderItems"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItems(Base):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(String, ForeignKey("order.order_id"))
    prod_id: Mapped[str] = mapped_column(String, ForeignKey("Product.prod_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    price: Mapped[float] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")