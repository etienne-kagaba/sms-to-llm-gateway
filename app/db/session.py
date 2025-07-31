from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

engine = create_async_engine(
    os.getenv("DATABASE_URL")
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
