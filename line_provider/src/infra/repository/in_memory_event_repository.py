import time
from typing import List, Dict, Optional

from src.domain.repository import BaseEventRepository
from src.domain.entity import Event
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventAlreadyExistsError
from decimal import Decimal

_EVENTS: Dict[int, Event] = {
    1: Event(event_id=1, coefficient=Decimal("1.20"), deadline=int(time.time()) + 600, status=EventStatus.NEW),
    2: Event(event_id=2, coefficient=Decimal("1.15"), deadline=int(time.time()) + 60, status=EventStatus.NEW),
    3: Event(event_id=3, coefficient=Decimal("1.67"), deadline=int(time.time()) + 90, status=EventStatus.NEW)
}

class InMemoryEventRepository(BaseEventRepository):

    def __init__(self, events: Dict[int, Event] = _EVENTS) -> None:
        """Initialize an empty event repository"""
        self._events: Dict[int, Event] = events

    async def get_all(self) -> List[Event]:
        """
        Get all events regardless of their status or deadline.

        Returns:
            List[Event]: List of all events in the repository
        """
        return list(self._events.values())

    async def get_active_events(self) -> List[Event]:
        """
        Get all active events (not finished and not expired).
        
        An event is considered active if:
        1. Its status is NEW
        2. Its deadline has not passed
        
        Returns:
            List[Event]: List of active events
        """
        return [event for event in self._events.values() if event.is_active]

    async def get_by_id(self, event_id: int) -> Event:
        """
        Get event by its ID.

        Args:
            event_id: Unique identifier of the event

        Returns:
            Event: The event if found

        Raises:
            EventNotFoundError: If event with given ID does not exist
        """
        event: Optional[Event] = self._events.get(event_id)
        if not event:
            raise EventNotFoundError(event_id)
        return event

    async def create(self, event: Event) -> Event:
        """
        Create a new event in the repository.

        Args:
            event: Event entity to create

        Returns:
            Event: Created event with any repository-specific fields populated

        Raises:
            EventAlreadyExistsError: If event with the same ID already exists
        """
        if await self.exists(event.event_id):
            raise EventAlreadyExistsError(event.event_id)
            
        self._events[event.event_id] = event
        return event

    async def update(self, event: Event) -> Event:
        """
        Update an existing event in the repository.

        Args:
            event: Event entity with updated data

        Returns:
            Event: Updated event

        Raises:
            EventNotFoundError: If event with given ID does not exist
        """
        if not await self.exists(event.event_id):
            raise EventNotFoundError(event.event_id)
            
        self._events[event.event_id] = event
        return event

    async def update_status(self, event_id: int, new_status: EventStatus) -> Event:
        """
        Update the status of an event.

        This is a specific update method for changing event status, following
        the principle of having focused repository methods that match domain operations.

        Args:
            event_id: ID of the event to update
            new_status: New status to set

        Returns:
            Event: Updated event

        Raises:
            EventNotFoundError: If event with given ID does not exist
        """
        event: Event = await self.get_by_id(event_id)
        event.status = new_status
        return event

    async def exists(self, event_id: int) -> bool:
        """
        Check if an event exists in the repository.

        Args:
            event_id: ID of the event to check

        Returns:
            bool: True if event exists, False otherwise
        """
        return event_id in self._events

    async def clear(self) -> None:
        """
        Remove all events from the repository.
        
        This is primarily useful for testing purposes.
        """
        self._events.clear()
