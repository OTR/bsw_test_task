from dataclasses import dataclass
from typing import List

from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus


@dataclass
class EventService:
    repository: BaseEventRepository

    async def get_all_events(self) -> List[Event]:
        """
        Get all events regardless of their status.

        Returns:
            List[Event]: All events in the system
        """
        return await self.repository.get_all()

    async def get_active_events(self) -> List[Event]:
        """
        Get all active events that are available for betting.
        
        An event is considered active if:
        1. Its status is NEW (not finished)
        2. Its deadline has not passed
        
        Returns:
            List[Event]: List of active events
        """
        return await self.repository.get_active_events()

    async def get_event(self, event_id: int) -> Event:
        """
        Get a specific event by its ID.

        Args:
            event_id: Unique identifier of the event

        Returns:
            Event: The requested event

        Raises:
            EventNotFoundError: If event with given ID does not exist
        """
        return await self.repository.get_by_id(event_id)

    async def create_event(self, event: Event) -> Event:
        """
        Create a new betting event.
        
        Args:
            event: Event to create
            
        Returns:
            Event: Created event
            
        Raises:
            EventAlreadyExistsError: If event with given ID already exists
            InvalidEventDeadlineError: If event deadline is not in the future
        """
        return await self.repository.create(event)

    async def update_event(self, event: Event) -> Event:
        """
        Update an existing betting event.
        
        Args:
            event: Event with updated data
            
        Returns:
            Event: Updated event
            
        Raises:
            EventNotFoundError: If event with given ID does not exist
            InvalidEventDeadlineError: If event deadline is not in the future
        """
        return await self.repository.update(event)

    async def finish_event(self, event_id: int, first_team_won: bool) -> Event:
        """
        Mark an event as finished with the specified outcome.

        Args:
            event_id: ID of the event to finish
            first_team_won: True if first team won, False if second team won

        Returns:
            Event: Updated event

        Raises:
            EventNotFoundError: If event with given ID does not exist
            ValueError: If event is already finished
        """
        event = await self.repository.get_by_id(event_id)
        if event.is_finished:
            raise ValueError(f"Event {event_id} is already finished")

        new_status = EventStatus.FINISHED_WIN if first_team_won else EventStatus.FINISHED_LOSE
        event.status = new_status
        
        return await self.repository.update(event)

    async def event_exists(self, event_id: int) -> bool:
        """
        Check if an event exists.
        
        Args:
            event_id: ID of the event to check
            
        Returns:
            bool: True if event exists, False otherwise
        """
        return await self.repository.exists(event_id)
