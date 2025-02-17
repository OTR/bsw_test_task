from datetime import datetime
from decimal import Decimal
from typing import List

import pytest
from unittest.mock import AsyncMock, Mock

from src.application.service import EventService
from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventAlreadyExistsError


pytestmark = pytest.mark.asyncio

@pytest.fixture
def future_timestamp() -> int:
    """Return a timestamp 1 hour in the future"""
    return int(datetime.now().timestamp()) + 3600


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create a mock repository that implements BaseEventRepository"""
    repository = AsyncMock(spec=BaseEventRepository)
    return repository


@pytest.fixture
def event_service(mock_repository: AsyncMock) -> EventService:
    """Create an EventService instance with a mock repository"""
    return EventService(repository=mock_repository)


@pytest.fixture
def sample_event(future_timestamp: int) -> Event:
    """Create a sample event with valid data"""
    return Event(
        event_id=1,
        coefficient=Decimal("1.50"),
        deadline=future_timestamp,
        status=EventStatus.NEW
    )


class TestEventService:
    """Test suite for EventService"""

    async def test_get_all_events(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        sample_event: Event
    ):
        """Should return all events from repository"""
        # Arrange
        mock_repository.get_all.return_value = [sample_event]

        # Act
        events = await event_service.get_all_events()

        # Assert
        assert events == [sample_event]
        mock_repository.get_all.assert_awaited_once()

    async def test_get_active_events(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        sample_event: Event
    ):
        """Should return active events from repository"""
        # Arrange
        mock_repository.get_active_events.return_value = [sample_event]

        # Act
        events = await event_service.get_active_events()

        # Assert
        assert events == [sample_event]
        mock_repository.get_active_events.assert_awaited_once()

    async def test_get_event_existing(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        sample_event: Event
    ):
        """Should return event when it exists"""
        # Arrange
        mock_repository.get_by_id.return_value = sample_event

        # Act
        event = await event_service.get_event(sample_event.event_id)

        # Assert
        assert event == sample_event
        mock_repository.get_by_id.assert_awaited_once_with(sample_event.event_id)

    async def test_get_event_not_found(
        self,
        event_service: EventService,
        mock_repository: AsyncMock
    ):
        """Should propagate EventNotFoundError from repository"""
        # Arrange
        event_id = 999
        mock_repository.get_by_id.side_effect = EventNotFoundError(event_id)

        # Act & Assert
        with pytest.raises(EventNotFoundError) as exc_info:
            await event_service.get_event(event_id)
        assert exc_info.value.event_id == event_id
        mock_repository.get_by_id.assert_awaited_once_with(event_id)

    async def test_create_event_success(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        future_timestamp: int
    ):
        """Should create event with correct parameters"""
        # Arrange
        event_id = 1
        coefficient = Decimal("1.50")
        expected_event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.create.return_value = expected_event
    
        # Act
        created_event = await event_service.create_event(expected_event)

        # Assert
        assert created_event == expected_event
        mock_repository.create.assert_awaited_once()
        created_event_arg = mock_repository.create.call_args[0][0]
        assert created_event_arg.event_id == event_id
        assert created_event_arg.coefficient == coefficient
        assert created_event_arg.deadline == future_timestamp

    async def test_create_event_already_exists(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        future_timestamp: int
    ):
        """Should propagate EventAlreadyExistsError from repository"""
        # Arrange
        event_id = 1
        event = Event(
            event_id=event_id,
            coefficient=Decimal("1.50"),
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.create.side_effect = EventAlreadyExistsError(event_id)
    
        # Act & Assert
        with pytest.raises(EventAlreadyExistsError) as exc_info:
            await event_service.create_event(event)
        assert exc_info.value.event_id == event_id

    async def test_update_event_success(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        future_timestamp: int
    ):
        """Should update event with correct parameters"""
        # Arrange
        event_id = 1
        coefficient = Decimal("1.75")  # Updated coefficient
        expected_event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.update.return_value = expected_event
    
        # Act
        updated_event = await event_service.update_event(expected_event)

        # Assert
        assert updated_event == expected_event
        mock_repository.update.assert_awaited_once()
        updated_event_arg = mock_repository.update.call_args[0][0]
        assert updated_event_arg.event_id == event_id
        assert updated_event_arg.coefficient == coefficient
        assert updated_event_arg.deadline == future_timestamp

    async def test_update_event_not_found(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        future_timestamp: int
    ):
        """Should propagate EventNotFoundError from repository"""
        # Arrange
        event_id = 1
        event = Event(
            event_id=event_id,
            coefficient=Decimal("1.75"),
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.update.side_effect = EventNotFoundError(event_id)
    
        # Act & Assert
        with pytest.raises(EventNotFoundError) as exc_info:
            await event_service.update_event(event)
        assert exc_info.value.event_id == event_id

    async def test_finish_event_win(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        sample_event: Event
    ):
        """Should update event status to FINISHED_WIN when first team wins"""
        # Arrange
        event_id = sample_event.event_id
        # Use a new event with NEW status (not finished)
        unfinished_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.NEW  # Make sure it's not already finished
        )
        mock_repository.get_by_id.return_value = unfinished_event
        
        expected_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.FINISHED_WIN
        )
        mock_repository.update.return_value = expected_event

        # Act
        updated_event = await event_service.finish_event(event_id, first_team_won=True)

        # Assert
        assert updated_event == expected_event
        mock_repository.get_by_id.assert_awaited_once_with(event_id)
        # Check that update was called with the correctly modified event
        mock_repository.update.assert_awaited_once()
        updated_arg = mock_repository.update.call_args[0][0]
        assert updated_arg.status == EventStatus.FINISHED_WIN

    async def test_finish_event_lose(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        sample_event: Event
    ):
        """Should update event status to FINISHED_LOSE when first team loses"""
        # Arrange
        event_id = sample_event.event_id
        # Use a new event with NEW status (not finished)
        unfinished_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.NEW  # Make sure it's not already finished
        )
        mock_repository.get_by_id.return_value = unfinished_event
        
        expected_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.FINISHED_LOSE
        )
        mock_repository.update.return_value = expected_event

        # Act
        updated_event = await event_service.finish_event(event_id, first_team_won=False)

        # Assert
        assert updated_event == expected_event
        mock_repository.get_by_id.assert_awaited_once_with(event_id)
        # Check that update was called with the correctly modified event
        mock_repository.update.assert_awaited_once()
        updated_arg = mock_repository.update.call_args[0][0]
        assert updated_arg.status == EventStatus.FINISHED_LOSE

    async def test_finish_event_already_finished(
        self,
        event_service: EventService,
        mock_repository: AsyncMock,
        sample_event: Event
    ):
        """Should raise ValueError when trying to finish an already finished event"""
        # Arrange
        event_id = sample_event.event_id
        finished_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.FINISHED_WIN
        )
        mock_repository.get_by_id.return_value = finished_event

        # Act & Assert
        with pytest.raises(ValueError, match=f"Event {event_id} is already finished"):
            await event_service.finish_event(event_id, first_team_won=True)
        mock_repository.get_by_id.assert_awaited_once_with(event_id)
        mock_repository.update.assert_not_awaited()

    async def test_event_exists(
        self,
        event_service: EventService,
        mock_repository: AsyncMock
    ):
        """Should check event existence through repository"""
        # Arrange
        event_id = 1
        mock_repository.exists.return_value = True

        # Act
        exists = await event_service.event_exists(event_id)

        # Assert
        assert exists is True
        mock_repository.exists.assert_awaited_once_with(event_id)