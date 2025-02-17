import time

from src.schemas import Event, EventStatus


events: dict[str, Event] = {
    '1': Event(event_id='1', coefficient=1.2, deadline=int(time.time()) + 600, status=EventStatus.NEW),
    '2': Event(event_id='2', coefficient=1.15, deadline=int(time.time()) + 60, status=EventStatus.NEW),
    '3': Event(event_id='3', coefficient=1.67, deadline=int(time.time()) + 90, status=EventStatus.NEW)
}
