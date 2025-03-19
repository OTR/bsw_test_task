from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.service import EventService
from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventAlreadyExistsError

pytestmark = pytest.mark.asyncio


@pytest.fixture
def future_timestamp():
    return int(datetime.now().timestamp()) + 3600


@pytest.fixture
def mock_repository():
    repository = AsyncMock(spec=BaseEventRepository)
    return repository


@pytest.fixture
def event_service(mock_repository):
    return EventService(repository=mock_repository)


@pytest.fixture
def sample_event(future_timestamp):
    return Event(
        event_id=1,
        coefficient=Decimal("1.50"),
        deadline=future_timestamp,
        status=EventStatus.NEW
    )


class TestEventService:
    async def test_get_all_events(self, event_service, mock_repository, sample_event):
        mock_repository.get_all.return_value = [sample_event]
        events = await event_service.get_all_events()
        assert events == [sample_event]
        mock_repository.get_all.assert_awaited_once()

    async def test_get_active_events(self, event_service, mock_repository, sample_event):
        mock_repository.get_active_events.return_value = [sample_event]
        events = await event_service.get_active_events()
        assert events == [sample_event]
        mock_repository.get_active_events.assert_awaited_once()

    async def test_get_event_existing(self, event_service, mock_repository, sample_event):
        mock_repository.get_by_id.return_value = sample_event
        event = await event_service.get_event(sample_event.event_id)
        assert event == sample_event
        mock_repository.get_by_id.assert_awaited_once_with(sample_event.event_id)

    async def test_get_event_not_found(self, event_service, mock_repository):
        event_id = 999
        mock_repository.get_by_id.side_effect = EventNotFoundError(event_id)
        with pytest.raises(EventNotFoundError) as exc_info:
            await event_service.get_event(event_id)
        assert exc_info.value.event_id == event_id
        mock_repository.get_by_id.assert_awaited_once_with(event_id)

    async def test_create_event_success(self, event_service, mock_repository, future_timestamp):
        event_id = 1
        coefficient = Decimal("1.50")
        expected_event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.create.return_value = expected_event
        created_event = await event_service.create_event(expected_event)
        assert created_event == expected_event
        mock_repository.create.assert_awaited_once()
        created_event_arg = mock_repository.create.call_args[0][0]
        assert created_event_arg.event_id == event_id
        assert created_event_arg.coefficient == coefficient
        assert created_event_arg.deadline == future_timestamp

    async def test_create_event_already_exists(self, event_service, mock_repository, future_timestamp):
        event_id = 1
        event = Event(
            event_id=event_id,
            coefficient=Decimal("1.50"),
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.create.side_effect = EventAlreadyExistsError(event_id)

        with pytest.raises(EventAlreadyExistsError) as exc_info:
            await event_service.create_event(event)
        assert exc_info.value.event_id == event_id

    async def test_update_event_success(self, event_service, mock_repository, future_timestamp):
        event_id = 1
        coefficient = Decimal("1.75")
        expected_event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.update.return_value = expected_event
        updated_event = await event_service.update_event(expected_event)
        assert updated_event == expected_event
        mock_repository.update.assert_awaited_once()
        updated_event_arg = mock_repository.update.call_args[0][0]
        assert updated_event_arg.event_id == event_id
        assert updated_event_arg.coefficient == coefficient
        assert updated_event_arg.deadline == future_timestamp

    async def test_update_event_not_found(self, event_service, mock_repository, future_timestamp):
        event_id = 1
        event = Event(
            event_id=event_id,
            coefficient=Decimal("1.75"),
            deadline=future_timestamp,
            status=EventStatus.NEW
        )
        mock_repository.update.side_effect = EventNotFoundError(event_id)
        with pytest.raises(EventNotFoundError) as exc_info:
            await event_service.update_event(event)
        assert exc_info.value.event_id == event_id

    async def test_finish_event_win(self, event_service, mock_repository, sample_event):
        event_id = sample_event.event_id
        unfinished_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.NEW
        )
        mock_repository.get_by_id.return_value = unfinished_event
        expected_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.FINISHED_WIN
        )
        mock_repository.update.return_value = expected_event
        updated_event = await event_service.finish_event(event_id, first_team_won=True)
        assert updated_event == expected_event
        mock_repository.get_by_id.assert_awaited_once_with(event_id)
        mock_repository.update.assert_awaited_once()
        updated_arg = mock_repository.update.call_args[0][0]
        assert updated_arg.status == EventStatus.FINISHED_WIN

    async def test_finish_event_lose(self, event_service, mock_repository, sample_event):
        event_id = sample_event.event_id
        unfinished_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.NEW
        )
        mock_repository.get_by_id.return_value = unfinished_event

        expected_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.FINISHED_LOSE
        )
        mock_repository.update.return_value = expected_event

        updated_event = await event_service.finish_event(event_id, first_team_won=False)

        assert updated_event == expected_event
        mock_repository.get_by_id.assert_awaited_once_with(event_id)
        mock_repository.update.assert_awaited_once()
        updated_arg = mock_repository.update.call_args[0][0]
        assert updated_arg.status == EventStatus.FINISHED_LOSE

    async def test_finish_event_already_finished(self, event_service, mock_repository, sample_event):
        event_id = sample_event.event_id
        finished_event = Event(
            event_id=event_id,
            coefficient=sample_event.coefficient,
            deadline=sample_event.deadline,
            status=EventStatus.FINISHED_WIN
        )
        mock_repository.get_by_id.return_value = finished_event

        with pytest.raises(ValueError, match=f"Событие {event_id} уже завершено"):
            await event_service.finish_event(event_id, first_team_won=True)
        mock_repository.get_by_id.assert_awaited_once_with(event_id)
        mock_repository.update.assert_not_awaited()

    async def test_event_exists(self, event_service, mock_repository):
        event_id = 1
        mock_repository.exists.return_value = True

        exists = await event_service.event_exists(event_id)

        assert exists is True
        mock_repository.exists.assert_awaited_once_with(event_id)
