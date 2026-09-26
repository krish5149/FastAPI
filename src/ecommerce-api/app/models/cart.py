import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Cart(Base):
    __tablename__ = "cart"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_code"))
    cart_id: Mapped[str] = mapped_column(String,primary_key=True, index=True)

    items: Mapped[list["CartItem"]] = relationship(back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_id: Mapped[str] = mapped_column(String, ForeignKey("cart.cart_id"))
    prod_id: Mapped[str] = mapped_column(String, ForeignKey("Product.prod_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    process_id: Mapped[uuid.UUID] = mapped_column(primary_key=True,default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    
    cart: Mapped["Cart"] = relationship(back_populates="items")