import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..models.product import Product
from ..models.cart import Cart
from ..models.order import Order
from ..models.review import Review

async def generate_unique_user_code(db: AsyncSession) -> int:
    while True:
        candidate_code = random.randint(10000, 99999)
        result = await db.execute(select(User).where(User.user_code == candidate_code))
        if result.scalar_one_or_none() is None:
            return candidate_code

async def generate_unique_product_code(db: AsyncSession) -> str:
    while True:
        product_code = f"PR{random.randint(100000, 999999)}"

        result = await db.execute(
            select(Product.prod_id).where(Product.prod_id == product_code)
        )

        if result.scalar_one_or_none() is None:
            return product_code

async def generate_unique_cart_code(db: AsyncSession) -> str:
    while True:
        cart_code = f"KT{random.randint(100000, 999999)}"

        result = await db.execute(
            select(Cart.cart_id).where(Cart.cart_id == cart_code)
        )

        if result.scalar_one_or_none() is None:
            return cart_code

async def generate_unique_order_code(db: AsyncSession) -> str:
    while True:
        order_code = f"ORD{random.randint(100000, 999999)}"

        result = await db.execute(
            select(Order.order_id).where(Order.order_id == order_code)
        )

        if result.scalar_one_or_none() is None:
            return order_code


async def generate_unique_review_code(db: AsyncSession) -> str:
    while True:
        review_code = f"RVW{random.randint(100000, 999999)}"

        result = await db.execute(
            select(Review.review_id).where(Review.review_id == review_code)
        )

        if result.scalar_one_or_none() is None:
            return review_code