from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, Mock

import pytest

from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventAlreadyExistsError, InvalidEventDeadlineError
from src.infra.repository import InMemoryEventRepository

pytestmark = pytest.mark.asyncio


def create_event(event_id: int, coefficient: Decimal, deadline: int, status: EventStatus = EventStatus.NEW) -> Event:
    return Event.model_construct(event_id=event_id, coefficient=coefficient, deadline=deadline, status=status)


@pytest.fixture
def future_timestamp() -> int:
    return int(datetime.now().timestamp()) + 3600


@pytest.fixture
def expired_timestamp() -> int:
    return int(datetime.now().timestamp()) - 3600


@pytest.fixture
def sample_event(future_timestamp: int) -> Event:
    return Event(event_id=1, coefficient=Decimal("1.50"), deadline=future_timestamp, status=EventStatus.NEW)


@pytest.fixture
def repository() -> InMemoryEventRepository:
    return InMemoryEventRepository({})


@pytest.fixture
def base_repository() -> BaseEventRepository:
    return InMemoryEventRepository({})


@pytest.fixture
def populated_repo(repository: InMemoryEventRepository, future_timestamp: int) -> InMemoryEventRepository:
    events = [
        Event(event_id=1, coefficient=Decimal("1.20"), deadline=future_timestamp, status=EventStatus.NEW),
        Event(event_id=2, coefficient=Decimal("1.15"), deadline=future_timestamp, status=EventStatus.FINISHED_WIN),
        Event(event_id=3, coefficient=Decimal("1.67"), deadline=future_timestamp, status=EventStatus.FINISHED_LOSE)
    ]
    for event in events:
        repository._events[event.event_id] = event
    return repository


class TestEventRepoInterface:
    async def test_get_all(self, base_repository: BaseEventRepository, sample_event: Event):
        await base_repository.create(sample_event)
        events = await base_repository.get_all()
        assert len(events) == 1
        assert events[0] == sample_event

    async def test_get_active_events(self, base_repository: BaseEventRepository, sample_event: Event, future_timestamp: int):
        active_event = sample_event
        inactive_event = Event(event_id=2, coefficient=Decimal("1.15"), deadline=future_timestamp, status=EventStatus.FINISHED_WIN)

        await base_repository.create(active_event)
        await base_repository.create(inactive_event)

        active_events = await base_repository.get_active_events()
        assert len(active_events) == 1
        assert active_events[0] == active_event

    async def test_get_by_id(self, base_repository: BaseEventRepository, sample_event: Event):
        await base_repository.create(sample_event)
        event = await base_repository.get_by_id(sample_event.event_id)
        assert event == sample_event

        with pytest.raises(EventNotFoundError):
            await base_repository.get_by_id(999)

    async def test_create(self, base_repository: BaseEventRepository, sample_event: Event):
        created_event = await base_repository.create(sample_event)
        assert created_event == sample_event
        assert await base_repository.exists(sample_event.event_id)

        with pytest.raises(EventAlreadyExistsError):
            await base_repository.create(sample_event)

    async def test_update_status(self, base_repository: BaseEventRepository, sample_event: Event):
        await base_repository.create(sample_event)
        updated_event = await base_repository.update_status(sample_event.event_id, EventStatus.FINISHED_WIN)
        assert updated_event.status == EventStatus.FINISHED_WIN

        retrieved_event = await base_repository.get_by_id(sample_event.event_id)
        assert retrieved_event.status == EventStatus.FINISHED_WIN

        with pytest.raises(EventNotFoundError):
            await base_repository.update_status(999, EventStatus.FINISHED_WIN)

    async def test_exists(self, base_repository: BaseEventRepository, sample_event: Event):
        assert not await base_repository.exists(sample_event.event_id)
        await base_repository.create(sample_event)
        assert await base_repository.exists(sample_event.event_id)

    async def test_clear(self, base_repository: BaseEventRepository, sample_event: Event):
        await base_repository.create(sample_event)
        assert len(await base_repository.get_all()) == 1

        await base_repository.clear()
        assert len(await base_repository.get_all()) == 0


class TestInMemoryEventRepo:
    async def test_get_all_empty(self, repository: InMemoryEventRepository):
        events = await repository.get_all()
        assert len(events) == 0
        assert isinstance(events, list)

    async def test_get_all_populated(self, populated_repo: InMemoryEventRepository):
        events = await populated_repo.get_all()
        assert len(events) == 3
        statuses = {event.status for event in events}
        assert statuses == {EventStatus.NEW, EventStatus.FINISHED_WIN, EventStatus.FINISHED_LOSE}

    async def test_get_active_events(self, repository: InMemoryEventRepository, future_timestamp: int):
        current_time = future_timestamp - 3600
        expired_deadline = current_time - 60

        mock_now = Mock()
        mock_now.timestamp.return_value = current_time

        with patch('src.domain.entity.event.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now

            events = [
                create_event(1, Decimal("1.20"), future_timestamp, EventStatus.NEW),
                create_event(2, Decimal("1.15"), future_timestamp, EventStatus.FINISHED_WIN),
                create_event(3, Decimal("1.67"), expired_deadline, EventStatus.NEW),
            ]

            for event in events:
                repository._events[event.event_id] = event

            active_events = await repository.get_active_events()
            assert len(active_events) == 1
            assert active_events[0].event_id == 1

    async def test_get_by_id_existing(self, populated_repo: InMemoryEventRepository):
        event = await populated_repo.get_by_id(1)
        assert event.event_id == 1
        assert event.coefficient == Decimal("1.20")
        assert event.status == EventStatus.NEW

    async def test_get_by_id_non_existing(self, repository: InMemoryEventRepository):
        with pytest.raises(EventNotFoundError) as exc_info:
            await repository.get_by_id(999)
        assert exc_info.value.event_id == 999

    async def test_create_new(self, repository: InMemoryEventRepository, sample_event: Event):
        created_event = await repository.create(sample_event)
        assert created_event == sample_event
        assert await repository.exists(sample_event.event_id)

    async def test_create_duplicate(self, repository: InMemoryEventRepository, sample_event: Event):
        await repository.create(sample_event)
        with pytest.raises(EventAlreadyExistsError) as exc_info:
            await repository.create(sample_event)
        assert exc_info.value.event_id == sample_event.event_id

    async def test_update_status_existing(self, populated_repo: InMemoryEventRepository):
        event = await populated_repo.update_status(1, EventStatus.FINISHED_WIN)
        assert event.status == EventStatus.FINISHED_WIN
        retrieved_event = await populated_repo.get_by_id(1)
        assert retrieved_event.status == EventStatus.FINISHED_WIN

    async def test_update_status_non_existing(self, repository: InMemoryEventRepository):
        with pytest.raises(EventNotFoundError) as exc_info:
            await repository.update_status(999, EventStatus.FINISHED_WIN)
        assert exc_info.value.event_id == 999

    async def test_exists_existing(self, populated_repo: InMemoryEventRepository):
        assert await populated_repo.exists(1)

    async def test_exists_non_existing(self, repository: InMemoryEventRepository):
        assert not await repository.exists(999)

    async def test_clear(self, populated_repo: InMemoryEventRepository):
        assert len(await populated_repo.get_all()) > 0
        await populated_repo.clear()
        assert len(await populated_repo.get_all()) == 0

    async def test_coefficient_validation(self, repository: InMemoryEventRepository, future_timestamp: int):
        with pytest.raises(ValueError):
            event = Event(event_id=1, coefficient=Decimal("0"), deadline=future_timestamp, status=EventStatus.NEW)
            await repository.create(event)

    async def test_deadline_validation(self, repository: InMemoryEventRepository, expired_timestamp: int):
        with pytest.raises(InvalidEventDeadlineError):
            event = Event(event_id=1, coefficient=Decimal("1.50"), deadline=expired_timestamp, status=EventStatus.NEW)
            await repository.create(event)
