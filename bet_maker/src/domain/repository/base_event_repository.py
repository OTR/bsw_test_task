from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from src.domain.entity import Event
from src.domain.vo import EventStatus


class BaseEventRepository(ABC):
    """
    Abstract base class for event repositories following the Repository pattern.
    
    This class defines the interface for accessing events regardless of the
    underlying data source (database, remote API, in-memory, etc.). It follows
    the Repository pattern from Domain-Driven Design to abstract the data access
    layer from the domain layer.
    
    Any concrete implementation of this repository should handle the specific
    data source interactions and mapping to/from the domain Event entity.
    """
    
    @abstractmethod
    async def get_all(self) -> List[Event]:
        """
        Retrieves all available events from the data source.
        
        Returns:
            A list of Event domain entities
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, event_id: int) -> Event:
        """
        Retrieves a specific event by its unique identifier.
        
        Args:
            event_id: The unique identifier of the event to retrieve
            
        Returns:
            The Event domain entity if found
            
        Raises:
            EventNotFoundError: If the event with the specified ID doesn't exist
            EventRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def get_active_events(self) -> List[Event]:
        """
        Retrieves all active events from the data source.
        Active events are those that have not yet started and are accepting bets.
        
        Returns:
            A list of active Event domain entities
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def filter_events(
        self,
        status: Optional[EventStatus] = None,
        deadline_before: Optional[datetime] = None,
        deadline_after: Optional[datetime] = None,
    ) -> List[Event]:
        """
        Retrieves events that match the specified filters.
        
        Args:
            status: Filter by event status, if provided
            deadline_before: Only include events with deadlines before this time, if provided
            deadline_after: Only include events with deadlines after this time, if provided
            
        Returns:
            A list of Event domain entities matching the filters
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def exists(self, event_id: int) -> bool:
        """
        Checks if an event with the specified ID exists.
        
        Args:
            event_id: The unique identifier of the event to check
            
        Returns:
            True if the event exists, False otherwise
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
