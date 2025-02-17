from datetime import datetime
from typing import Optional, List

from fastapi import status
from httpx import HTTPStatusError

from src.domain.entity import Event
from src.domain.vo import EventStatus
from src.domain.repository import BaseEventRepository
from src.exception import EventNotFoundError, EventRepositoryConnectionError
from src.infra.http import HTTPClient


class RemoteEventRepository(BaseEventRepository):
    
    def __init__(self, http_client: HTTPClient):
        """
        Initialize the remote event repository with an HTTP client.
        
        Args:
            http_client: The HTTP client to use for making requests to the remote service
        """
        self.http_client: HTTPClient = http_client
    
    async def get_all(self) -> List[Event]:
        """
        Retrieves all available events from the remote line-provider service.
        
        Returns:
            A list of Event domain entities
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the remote service
        """
        try:
            events: List[Event] = await self.http_client.get_model_list("/api/v1/events", Event)
            return events
        except Exception as err:
            raise EventRepositoryConnectionError(source="remote-line-provider", message=str(err)) from err
    
    async def get_by_id(self, event_id: int) -> Event:
        """
        Retrieves a specific event by its unique identifier from the remote service.
        
        Args:
            event_id: The unique identifier of the event to retrieve
            
        Returns:
            The Event domain entity if found
            
        Raises:
            EventNotFoundError: If the event with the specified ID doesn't exist
            EventRepositoryConnectionError: If there's an issue connecting to the remote service
        """
        try:
            event: Event = await self.http_client.get_model(f"/api/v1/event/{event_id}", Event)
            return event
        except HTTPStatusError as err:
            if err.response.status_code == status.HTTP_404_NOT_FOUND:
                raise EventNotFoundError(event_id=event_id) from err
            raise EventRepositoryConnectionError(source="remote-line-provider", message=str(err)) from err
        except Exception as err:
            raise EventRepositoryConnectionError(source="remote-line-provider", message=str(err)) from err
    
    async def get_active_events(self) -> List[Event]:
        """
        Retrieves all active events from the remote service.
        Active events are those that have not yet started and are accepting bets.
        
        Returns:
            A list of active Event domain entities
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the remote service
        """
        all_events: List[Event] = await self.get_all()
        return [event for event in all_events if event.is_active]
    
    async def filter_events(
        self,
        status: Optional[EventStatus] = None,
        deadline_before: Optional[datetime] = None,
        deadline_after: Optional[datetime] = None,
    ) -> List[Event]:
        """
        Retrieves events that match the specified filters from the remote service.
        
        Args:
            status: Filter by event status, if provided
            deadline_before: Only include events with deadlines before this time, if provided
            deadline_after: Only include events with deadlines after this time, if provided
            
        Returns:
            A list of Event domain entities matching the filters
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the remote service
        """
        all_events: List[Event] = await self.get_all()
        
        filtered_events: List[Event] = all_events
        
        if status is not None:
            filtered_events = [event for event in filtered_events if event.status == status]
        
        if deadline_before is not None:
            before_timestamp: int = int(deadline_before.timestamp())
            filtered_events = [event for event in filtered_events if event.deadline < before_timestamp]
        
        if deadline_after is not None:
            after_timestamp: int = int(deadline_after.timestamp())
            filtered_events = [event for event in filtered_events if event.deadline > after_timestamp]
        
        return filtered_events
    
    async def exists(self, event_id: int) -> bool:
        """
        Checks if an event with the specified ID exists in the remote service.
        
        Args:
            event_id: The unique identifier of the event to check
            
        Returns:
            True if the event exists, False otherwise
            
        Raises:
            EventRepositoryConnectionError: If there's an issue connecting to the remote service
        """
        try:
            await self.get_by_id(event_id)
            return True
        except EventNotFoundError:
            return False
