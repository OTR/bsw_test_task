from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import AsyncSessionLocal

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить экземпляр сессии к базе данных"""
    async with AsyncSessionLocal() as session:
        yield session
