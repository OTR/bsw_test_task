from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.domain.repository import BaseEventRepository
from src.domain.entity import Event
from src.domain.vo import EventStatus


@dataclass
class EventService:
    repository: BaseEventRepository

    async def get_all(self) -> List[Event]:
        """
        Get all events from the repository.
        
        Returns:
            A list of all Event entities
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the repository
        """
        return await self.repository.get_all()

    async def get_active_events(self) -> List[Event]:
        """
        Get only active events that are available for betting.
        An event is considered active if it has a status of NEW and
        its deadline is in the future.
        
        Returns:
            A list of active Event entities
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the repository
        """
        # Leverage the repository's dedicated method for efficiency
        return await self.repository.get_active_events()
    
    async def get_events_by_status(self, status: EventStatus) -> List[Event]:
        """
        Get events with the specified status.
        
        Args:
            status: The status to filter by
            
        Returns:
            A list of Event entities with the specified status
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the repository
        """
        return await self.repository.filter_events(status=status)
    
    async def get_events_by_deadline(
        self, 
        before: Optional[datetime] = None, 
        after: Optional[datetime] = None
    ) -> List[Event]:
        """
        Get events with deadlines within a specified time range.
        
        Args:
            before: If provided, only include events with deadlines before this time
            after: If provided, only include events with deadlines after this time
            
        Returns:
            A list of Event entities matching the deadline criteria
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the repository
        """
        return await self.repository.filter_events(
            deadline_before=before,
            deadline_after=after
        )
    
    async def get_event_by_id(self, event_id: int) -> Event:
        """
        Get a specific event by its ID.
        
        Args:
            event_id: The unique identifier of the event
            
        Returns:
            The Event entity if found
            
        Raises:
            EventNotFoundError: If the event with the specified ID doesn't exist
            EventRepositoryConnectionError: If there's an issue connecting to the repository
        """
        return await self.repository.get_by_id(event_id)
