import time

from fastapi import APIRouter, Path
from fastapi.exceptions import HTTPException

from src.schemas import Event
from src.storage import events

router = APIRouter(tags=["Betting Events"])

@router.put('/event')
async def create_event(event: Event) -> dict:
    """Динамически создать новое событие или изменить статус существующего"""
    if event.event_id not in events:
        events[event.event_id] = event
        return {}

    for p_name, p_value in event.model_dump(exclude_unset=True).items():
        setattr(events[event.event_id], p_name, p_value)

    return {}


@router.get('/event/{event_id}', response_model=Event)
async def get_event(event_id: str = Path()) -> Event:
    """Получить событие по ID"""
    if event_id in events:
        return events[event_id]

    raise HTTPException(status_code=404, detail="Event not found")


@router.get('/events')
async def get_events() -> list[Event]:
    """Получить все события"""
    return list(e for e in events.values()) # if time.time() < e.deadline)
