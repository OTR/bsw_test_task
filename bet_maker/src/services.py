import asyncio
import httpx
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import status

from src.models import Bet, BetStatus
from src.dependecies import get_session
from src.config import settings


async def fetch_events() -> list:
    """Получить события из сервиса line-provider"""
    url = f"{settings.LINE_PROVIDER_URL}/api/v1/events"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
    if response.status_code == status.HTTP_200_OK:
        return response.json()
    else:
        return []


async def update_bets(session: AsyncSession) -> None:
    """Обновить статусы ставок на основании завершенных событий"""
    events: list = await fetch_events()
    finished_events: dict[str, str] = {e.event_id: e.state for e in events if e.is_finished}

    if not finished_events:
        return None

    stmt = select(Bet).where(Bet.status == BetStatus.PENDING)
    result = session.execute(stmt)
    pending_bets: list[Bet] = result.scalars().all()

    for bet in pending_bets:
        if bet.event_id in finished_events:
            new_status = BetStatus.from_event_state(finished_events[bet.event_id])
            bet.status = new_status
    
    await session.commit()


async def poll_events():
    """Периодически запрашивать события"""
    while True:
        async with get_session() as session:
            await update_bets()
        await asyncio.sleep(settings.EVENT_POLL_INTERVAL)
