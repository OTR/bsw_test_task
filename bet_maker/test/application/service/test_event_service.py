import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from src.application.service.event_service import EventService
from src.domain.entity.event import Event
from src.domain.vo.event_status import EventStatus
from src.exception import EventNotFoundError, EventRepositoryConnectionError


@pytest.fixture
def mock_event_repository():
    """Create a mock event repository with predefined behavior"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def event_service(mock_event_repository):
    """Create an EventService instance with a mock repository"""
    return EventService(repository=mock_event_repository)


@pytest.fixture
def sample_events():
    """Create sample events for testing"""
    now = datetime.now()
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    
    # Create events with different statuses and deadlines
    return [
        Event(
            event_id=1,
            coefficient=Decimal("1.50"),
            deadline=int(future.timestamp()),
            status=EventStatus.NEW
        ),
        Event(
            event_id=2,
            coefficient=Decimal("2.00"),
            deadline=int(future.timestamp()),
            status=EventStatus.FINISHED_WIN
        ),
        Event(
            event_id=3,
            coefficient=Decimal("3.00"),
            deadline=int(past.timestamp()),
            status=EventStatus.NEW
        ),
        Event(
            event_id=4,
            coefficient=Decimal("4.00"),
            deadline=int(past.timestamp()),
            status=EventStatus.FINISHED_LOSE
        ),
    ]


class TestEventService:
    """Test suite for the EventService class"""
    
    @pytest.mark.asyncio
    async def test_get_all(self, event_service, mock_event_repository, sample_events):
        """
        GIVEN a repository with events
        WHEN get_all() is called
        THEN it should return all events from the repository
        """
        # Arrange
        mock_event_repository.get_all.return_value = sample_events
        
        # Act
        result = await event_service.get_all()
        
        # Assert
        assert result == sample_events
        mock_event_repository.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_with_error(self, event_service, mock_event_repository):
        """
        GIVEN a repository that raises an error
        WHEN get_all() is called
        THEN it should propagate the error
        """
        # Arrange
        mock_event_repository.get_all.side_effect = EventRepositoryConnectionError(
            source="test", message="Test connection error"
        )
        
        # Act & Assert
        with pytest.raises(EventRepositoryConnectionError):
            await event_service.get_all()
    
    @pytest.mark.asyncio
    async def test_get_active_events(self, event_service, mock_event_repository, sample_events):
        """
        GIVEN a repository with active and inactive events
        WHEN get_active_events() is called
        THEN it should return only active events
        """
        # Arrange
        active_events = [sample_events[0]]  # Only the first event is active
        mock_event_repository.get_active_events.return_value = active_events
        
        # Act
        result = await event_service.get_active_events()
        
        # Assert
        assert result == active_events
        mock_event_repository.get_active_events.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_by_status(self, event_service, mock_event_repository, sample_events):
        """
        GIVEN a repository with events of different statuses
        WHEN get_events_by_status() is called with a specific status
        THEN it should return only events with that status
        """
        # Arrange
        new_events = [e for e in sample_events if e.status == EventStatus.NEW]
        mock_event_repository.filter_events.return_value = new_events
        
        # Act
        result = await event_service.get_events_by_status(EventStatus.NEW)
        
        # Assert
        assert result == new_events
        mock_event_repository.filter_events.assert_called_once_with(
            status=EventStatus.NEW
        )
    
    @pytest.mark.asyncio
    async def test_get_events_by_deadline(self, event_service, mock_event_repository, sample_events):
        """
        GIVEN a repository with events with different deadlines
        WHEN get_events_by_deadline() is called with before and after dates
        THEN it should return events within that date range
        """
        # Arrange
        now = datetime.now()
        mock_event_repository.filter_events.return_value = [sample_events[0], sample_events[1]]
        
        # Act
        result = await event_service.get_events_by_deadline(
            before=now + timedelta(days=2),
            after=now
        )
        
        # Assert
        assert result == [sample_events[0], sample_events[1]]
        mock_event_repository.filter_events.assert_called_once_with(
            deadline_before=now + timedelta(days=2),
            deadline_after=now
        )
    
    @pytest.mark.asyncio
    async def test_get_event_by_id(self, event_service, mock_event_repository, sample_events):
        """
        GIVEN a repository with events
        WHEN get_event_by_id() is called with a valid ID
        THEN it should return the event with that ID
        """
        # Arrange
        event = sample_events[0]
        mock_event_repository.get_by_id.return_value = event
        
        # Act
        result = await event_service.get_event_by_id(1)
        
        # Assert
        assert result == event
        mock_event_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_event_by_id_not_found(self, event_service, mock_event_repository):
        """
        GIVEN a repository where an event doesn't exist
        WHEN get_event_by_id() is called with a non-existent ID
        THEN it should raise EventNotFoundError
        """
        # Arrange
        mock_event_repository.get_by_id.side_effect = EventNotFoundError(event_id=999)
        
        # Act & Assert
        with pytest.raises(EventNotFoundError) as exc_info:
            await event_service.get_event_by_id(999)
        
        assert "999" in str(exc_info.value)