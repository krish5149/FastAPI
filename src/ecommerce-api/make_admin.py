import asyncio
from sqlalchemy import select
from .app.database import async_session
from .app.models.user import User, UserRole

async def make_admin(email: str):
    async with async_session() as db:
        user = await db.scalar(select(User).where(User.email == email))
        if not user:
            print("No user found with that email")
            return
        user.role = UserRole.admin
        await db.commit()
        print(f"{user.email} is now admin")

asyncio.run(make_admin("admin@bay.com"))