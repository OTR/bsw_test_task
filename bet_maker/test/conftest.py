from decimal import Decimal
from datetime import datetime
from typing import AsyncGenerator, List

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import event

from src.domain.entity import Bet
from src.domain.vo import BetStatus
from src.infra.database.bet_model import BetModel
from src.infra.database.base_model import Base


# Fixture for in-memory SQLite database
@pytest_asyncio.fixture(scope="function")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session_factory(async_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(async_session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def sample_bet_models() -> List[BetModel]:
    return [
        BetModel(bet_id=1, event_id=101, amount=Decimal("100.00"), status=BetStatus.PENDING, created_at=datetime(2023, 1, 1, 12, 0, 0)),
        BetModel(bet_id=2, event_id=102, amount=Decimal("50.00"), status=BetStatus.WON, created_at=datetime(2023, 1, 2, 12, 0, 0)),
        BetModel(bet_id=3, event_id=101, amount=Decimal("75.00"), status=BetStatus.LOST, created_at=datetime(2023, 1, 3, 12, 0, 0)),
        BetModel(bet_id=4, event_id=103, amount=Decimal("200.00"), status=BetStatus.PENDING, created_at=datetime(2023, 1, 4, 12, 0, 0)),
    ]


@pytest.fixture
def sample_bets() -> List[Bet]:
    return [
        Bet(bet_id=1, event_id=101, amount=Decimal("100.00"), status=BetStatus.PENDING, created_at=datetime(2023, 1, 1, 12, 0, 0)),
        Bet(bet_id=2, event_id=102, amount=Decimal("50.00"), status=BetStatus.WON, created_at=datetime(2023, 1, 2, 12, 0, 0)),
        Bet(bet_id=3, event_id=101, amount=Decimal("75.00"), status=BetStatus.LOST, created_at=datetime(2023, 1, 3, 12, 0, 0)),
        Bet(bet_id=4, event_id=103, amount=Decimal("200.00"), status=BetStatus.PENDING, created_at=datetime(2023, 1, 4, 12, 0, 0)),
    ]


@pytest_asyncio.fixture
async def populated_db(db_session, sample_bet_models):
    session = db_session
    for bet_model in sample_bet_models:
        session.add(bet_model)

    await session.commit()
    return session
