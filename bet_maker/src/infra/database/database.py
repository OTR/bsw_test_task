from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy import text

from src.config import settings

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def initialize_database() -> None:
    """
    Эта функция должна вызываться при запуске приложения для проверки готовности базы данных.
    """
    session = AsyncSessionLocal()
    try:
        await session.execute(text("SELECT 1"))
        await session.commit()
    except Exception as e:
        raise RuntimeError(f"Ошибка инициализации базы данных: {str(e)}") from e
    finally:
        await session.close()


async def close_database_connection() -> None:
    await engine.dispose()
