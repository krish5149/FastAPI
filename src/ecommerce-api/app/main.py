from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import engine
from .models.user import Base
from .endpoints import auth, user, products, carts, orders, reviews
from .core.ExceptionHandler import AppException, app_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs once on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Ecommerce API", lifespan=lifespan)
app.add_exception_handler(AppException,app_exception_handler)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(products.router)
app.include_router(carts.router)
app.include_router(orders.router)
app.include_router(reviews.router)