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

# Configure the async engine with appropriate settings
# Note: For AsyncEngine, we don't explicitly specify poolclass as asyncio has its own pooling
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL query logging (development only)
    pool_size=5,  # Default connection pool size
    max_overflow=10,  # Allow up to 10 connections to be created when the pool is full
    pool_timeout=30,  # Timeout for getting a connection from the pool
    pool_recycle=1800,  # Recycle connections after 30 minutes to avoid stale connections
    pool_pre_ping=True,  # Verify connections before use to prevent using stale connections
)

# Create a sessionmaker factory
# - autoflush=False: Prevents automatic flushing when queries are executed
# - autocommit=False: Prevents automatic commit after each operation
# - expire_on_commit=False: Prevents expiring objects after commit, useful for async operations
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.
    
    Creates a new database session and closes it after use, handling
    commits and rollbacks automatically.
    
    Yields:
        AsyncSession: SQLAlchemy async session object
        
    Example:
        async with get_db_session() as session:
            result = await session.execute(...)
    """
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
    Initialize the database and perform startup checks.
    
    This function should be called during application startup to ensure
    the database is ready for use.
    """
    # Add any database initialization logic here
    # For example, checking database connectivity
    session = AsyncSessionLocal()
    try:
        # Simple connectivity check - using text() to create proper SQL expression
        await session.execute(text("SELECT 1"))
        await session.commit()
    except Exception as e:
        # Log the error or handle it appropriately
        raise RuntimeError(f"Database initialization failed: {str(e)}") from e
    finally:
        await session.close()


async def close_database_connection() -> None:
    """
    Close all database connections.
    
    This function should be called during application shutdown to ensure
    all database resources are properly released.
    """
    # Dispose the engine, closing all connections in the pool
    await engine.dispose()
