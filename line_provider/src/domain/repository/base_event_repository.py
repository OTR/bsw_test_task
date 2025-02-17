from abc import ABC, abstractmethod
from typing import List

from src.domain.entity import Event
from src.domain.vo import EventStatus

class BaseEventRepository(ABC):

    @abstractmethod
    async def get_all(self) -> List[Event]:
        """
        Get all events regardless of their status or deadline.

        Returns:
            List[Event]: List of all events in the repository
        """
        raise NotImplementedError

    @abstractmethod
    async def get_active_events(self) -> List[Event]:
        """
        Get all active events (not finished and not expired).
        
        An event is considered active if:
        1. Its status is NEW
        2. Its deadline has not passed
        
        Returns:
            List[Event]: List of active events
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def exists(self, event_id: int) -> bool:
        """
        Check if an event exists in the repository.

        Args:
            event_id: ID of the event to check

        Returns:
            bool: True if event exists, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """
        Remove all events from the repository.
        
        This is primarily useful for testing purposes.
        """
        raise NotImplementedError
