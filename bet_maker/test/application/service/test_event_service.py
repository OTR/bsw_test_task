import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

from src.application.service import EventService
from src.domain.entity import Event
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventRepositoryConnectionError


@pytest.fixture
def mock_event_repository():
    return AsyncMock()


@pytest.fixture
def event_service(mock_event_repository):
    return EventService(repository=mock_event_repository)


@pytest.fixture
def sample_events():
    now = datetime.now()
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    
    return [
        Event(event_id=1, coefficient=Decimal("1.50"), deadline=int(future.timestamp()), status=EventStatus.NEW),
        Event(event_id=2, coefficient=Decimal("2.00"), deadline=int(future.timestamp()), status=EventStatus.FINISHED_WIN),
        Event(event_id=3, coefficient=Decimal("3.00"), deadline=int(past.timestamp()), status=EventStatus.NEW),
        Event(event_id=4, coefficient=Decimal("4.00"), deadline=int(past.timestamp()), status=EventStatus.FINISHED_LOSE),
    ]


class TestEventService:
    @pytest.mark.asyncio
    async def test_get_all(self, event_service, mock_event_repository, sample_events):
        mock_event_repository.get_all.return_value = sample_events
        
        result = await event_service.get_all()
        
        assert result == sample_events
        mock_event_repository.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_with_error(self, event_service, mock_event_repository):
        mock_event_repository.get_all.side_effect = EventRepositoryConnectionError(
            source="test", message="Test connection error"
        )
        
        with pytest.raises(EventRepositoryConnectionError):
            await event_service.get_all()
    
    @pytest.mark.asyncio
    async def test_get_active_events(self, event_service, mock_event_repository, sample_events):
        active_events = [sample_events[0]]
        mock_event_repository.get_active_events.return_value = active_events
        
        result = await event_service.get_active_events()
        
        assert result == active_events
        mock_event_repository.get_active_events.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_by_status(self, event_service, mock_event_repository, sample_events):
        new_events = [e for e in sample_events if e.status == EventStatus.NEW]
        mock_event_repository.filter_events.return_value = new_events
        
        result = await event_service.get_events_by_status(EventStatus.NEW)
        
        assert result == new_events
        mock_event_repository.filter_events.assert_called_once_with(
            status=EventStatus.NEW
        )
    
    @pytest.mark.asyncio
    async def test_get_events_by_deadline(self, event_service, mock_event_repository, sample_events):
        now = datetime.now()
        mock_event_repository.filter_events.return_value = [sample_events[0], sample_events[1]]
        
        result = await event_service.get_events_by_deadline(
            before=now + timedelta(days=2),
            after=now
        )
        
        assert result == [sample_events[0], sample_events[1]]
        mock_event_repository.filter_events.assert_called_once_with(
            deadline_before=now + timedelta(days=2),
            deadline_after=now
        )
    
    @pytest.mark.asyncio
    async def test_get_event_by_id(self, event_service, mock_event_repository, sample_events):
        event = sample_events[0]
        mock_event_repository.get_by_id.return_value = event
        
        result = await event_service.get_event_by_id(1)
        
        assert result == event
        mock_event_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_event_by_id_not_found(self, event_service, mock_event_repository):
        mock_event_repository.get_by_id.side_effect = EventNotFoundError(event_id=999)
        
        with pytest.raises(EventNotFoundError) as exc_info:
            await event_service.get_event_by_id(999)
        
        assert "999" in str(exc_info.value)
