import time
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import Bet
from src.schemas import BetStatus, BetRequest, BetResponse
from src.dependecies import get_session
from src.config import settings
from src.services import fetch_events

router = APIRouter(tags=["Bet Maker"])

@router.get("/events")
async def get_alailable_events() -> list:
    """Получить список событий доступных для ставки"""
    events: list = await fetch_events()
    print(events)
    available_events: list = [e for e in events if e.get('status', "") == "NEW"]

    return available_events

@router.post("/bet")
async def create_bet(bet_in: BetRequest, session: AsyncSession = Depends(get_session)) -> dict:
    """Разместить новую ставку на событие по ID события"""
    async with httpx.AsyncClient() as client:
        url = f"{settings.LINE_PROVIDER_URL}/api/v1/event/{bet_in.event_id}"
        response = await client.get(url)

    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Betting event by ID not found")

    event = response.json()

    if event["status"] != "NEW" or event["deadline"] < time.time():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ставки больше не принимаются")
    
    new_bet = Bet(event_id=bet_in.event_id, amount=bet_in.amount)
    session.add(new_bet)
    await session.commit()
    await session.refresh(new_bet)

    return {
        "success": True,
        "data": {
            "bet_id": new_bet.bet_id
            }
        }


@router.get("/bets", response_model=List[BetResponse])
async def get_all_bets(session: AsyncSession = Depends(get_session)) -> List[BetResponse]:
    """Получить историю ставок"""
    stmt = select(Bet).order_by(Bet.created_at.desc()).limit(100)
    result = await session.execute(stmt)
    bets = result.scalars().all()

    return [BetResponse.model_validate(bet, from_attributes=True) for bet in bets]
