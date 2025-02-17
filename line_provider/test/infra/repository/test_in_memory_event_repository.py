from datetime import datetime
from unittest.mock import patch, Mock

from src.exception.exceptions import InvalidEventDeadlineError
import pytest
from decimal import Decimal

from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventAlreadyExistsError
from src.infra.repository import InMemoryEventRepository

def create_test_event(
    event_id: int,
    coefficient: Decimal,
    deadline: int,
    status: EventStatus = EventStatus.NEW
) -> Event:
    """Create an Event instance for testing, bypassing deadline validation"""
    return Event.model_construct(
        event_id=event_id,
        coefficient=coefficient,
        deadline=deadline,
        status=status
    )

pytestmark = pytest.mark.asyncio

@pytest.fixture
def future_timestamp() -> int:
    """Return a timestamp 1 hour in the future"""
    return int(datetime.now().timestamp()) + 3600


@pytest.fixture
def expired_timestamp() -> int:
    """Return a timestamp 1 hour in the past"""
    return int(datetime.now().timestamp()) - 3600


@pytest.fixture
def sample_event(future_timestamp: int) -> Event:
    """Create a sample event with valid data"""
    return Event(
        event_id=1,
        coefficient=Decimal("1.50"),
        deadline=future_timestamp,
        status=EventStatus.NEW
    )


@pytest.fixture
def repository() -> InMemoryEventRepository:
    """Create an empty repository for testing implementation details"""
    repo = InMemoryEventRepository({})  # Empty initial state
    return repo


@pytest.fixture
def base_repository() -> BaseEventRepository:
    """Create a repository instance as BaseEventRepository for interface testing"""
    return InMemoryEventRepository({})


@pytest.fixture
def populated_repository(repository: InMemoryEventRepository, future_timestamp: int) -> InMemoryEventRepository:
    """Create a repository pre-populated with test events"""
    events = [
        Event(event_id=1, coefficient=Decimal("1.20"), deadline=future_timestamp, status=EventStatus.NEW),
        Event(event_id=2, coefficient=Decimal("1.15"), deadline=future_timestamp, status=EventStatus.FINISHED_WIN),
        Event(event_id=3, coefficient=Decimal("1.67"), deadline=future_timestamp, status=EventStatus.FINISHED_LOSE)
    ]
    for event in events:
        repository._events[event.event_id] = event
    return repository


class TestEventRepositoryInterface:
    """Test suite verifying that InMemoryEventRepository correctly implements BaseEventRepository interface"""

    async def test_interface_get_all(self, base_repository: BaseEventRepository, sample_event: Event):
        """Should implement get_all() according to interface contract"""
        await base_repository.create(sample_event)
        events = await base_repository.get_all()
        assert len(events) == 1
        assert events[0] == sample_event

    async def test_interface_get_active_events(
        self, 
        base_repository: BaseEventRepository, 
        sample_event: Event,
        future_timestamp: int
    ):
        """Should implement get_active_events() according to interface contract"""
        # Create mix of active and inactive events
        active_event = sample_event
        inactive_event = Event(
            event_id=2,
            coefficient=Decimal("1.15"),
            deadline=future_timestamp,
            status=EventStatus.FINISHED_WIN
        )
        
        await base_repository.create(active_event)
        await base_repository.create(inactive_event)
        
        active_events = await base_repository.get_active_events()
        assert len(active_events) == 1
        assert active_events[0] == active_event

    async def test_interface_get_by_id(self, base_repository: BaseEventRepository, sample_event: Event):
        """Should implement get_by_id() according to interface contract"""
        await base_repository.create(sample_event)
        event = await base_repository.get_by_id(sample_event.event_id)
        assert event == sample_event

        with pytest.raises(EventNotFoundError):
            await base_repository.get_by_id(999)

    async def test_interface_create(self, base_repository: BaseEventRepository, sample_event: Event):
        """Should implement create() according to interface contract"""
        created_event = await base_repository.create(sample_event)
        assert created_event == sample_event
        assert await base_repository.exists(sample_event.event_id)

        with pytest.raises(EventAlreadyExistsError):
            await base_repository.create(sample_event)

    async def test_interface_update_status(
        self, 
        base_repository: BaseEventRepository, 
        sample_event: Event
    ):
        """Should implement update_status() according to interface contract"""
        await base_repository.create(sample_event)
        updated_event = await base_repository.update_status(sample_event.event_id, EventStatus.FINISHED_WIN)
        assert updated_event.status == EventStatus.FINISHED_WIN
        
        retrieved_event = await base_repository.get_by_id(sample_event.event_id)
        assert retrieved_event.status == EventStatus.FINISHED_WIN

        with pytest.raises(EventNotFoundError):
            await base_repository.update_status(999, EventStatus.FINISHED_WIN)

    async def test_interface_exists(self, base_repository: BaseEventRepository, sample_event: Event):
        """Should implement exists() according to interface contract"""
        assert not await base_repository.exists(sample_event.event_id)
        await base_repository.create(sample_event)
        assert await base_repository.exists(sample_event.event_id)

    async def test_interface_clear(self, base_repository: BaseEventRepository, sample_event: Event):
        """Should implement clear() according to interface contract"""
        await base_repository.create(sample_event)
        assert len(await base_repository.get_all()) == 1
        
        await base_repository.clear()
        assert len(await base_repository.get_all()) == 0


class TestInMemoryEventRepository:
    """Test suite for InMemoryEventRepository implementation"""

    async def test_get_all_empty_repository(self, repository: InMemoryEventRepository):
        """Should return empty list when repository is empty"""
        events = await repository.get_all()
        assert len(events) == 0
        assert isinstance(events, list)

    async def test_get_all_populated_repository(self, populated_repository: InMemoryEventRepository):
        """Should return all events regardless of status"""
        events = await populated_repository.get_all()
        assert len(events) == 3
        statuses = {event.status for event in events}
        assert statuses == {EventStatus.NEW, EventStatus.FINISHED_WIN, EventStatus.FINISHED_LOSE}

    async def test_get_active_events_returns_only_active(
        self, 
        repository: InMemoryEventRepository, 
        future_timestamp: int
    ):
        """Should return only events that are NEW and not expired"""
        # Create mix of active and inactive events
        current_time = future_timestamp - 3600  # 1 hour before future_timestamp
        expired_deadline = current_time - 60  # 1 minute before current_time
        
        # Mock datetime.now() for is_active check
        mock_now = Mock()
        mock_now.timestamp.return_value = current_time
        
        with patch('src.domain.entity.event.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            
            # Create events using test helper to bypass validation
            events = [
                create_test_event(1, Decimal("1.20"), future_timestamp, EventStatus.NEW),  # Active
                create_test_event(2, Decimal("1.15"), future_timestamp, EventStatus.FINISHED_WIN),  # Inactive (finished)
                create_test_event(3, Decimal("1.67"), expired_deadline, EventStatus.NEW),  # Inactive (expired)
            ]
            
            # Store events in repository
            for event in events:
                repository._events[event.event_id] = event

            # Test get_active_events under the same mock
            active_events = await repository.get_active_events()
            assert len(active_events) == 1
            assert active_events[0].event_id == 1

    async def test_get_by_id_existing_event(self, populated_repository: InMemoryEventRepository):
        """Should return event when it exists"""
        event = await populated_repository.get_by_id(1)
        assert event.event_id == 1
        assert event.coefficient == Decimal("1.20")
        assert event.status == EventStatus.NEW

    async def test_get_by_id_non_existing_event(self, repository: InMemoryEventRepository):
        """Should raise EventNotFoundError when event doesn't exist"""
        with pytest.raises(EventNotFoundError) as exc_info:
            await repository.get_by_id(999)
        assert exc_info.value.event_id == 999

    async def test_create_new_event(self, repository: InMemoryEventRepository, sample_event: Event):
        """Should successfully create new event"""
        created_event = await repository.create(sample_event)
        assert created_event == sample_event
        assert await repository.exists(sample_event.event_id)

    async def test_create_duplicate_event(self, repository: InMemoryEventRepository, sample_event: Event):
        """Should raise EventAlreadyExistsError when creating duplicate event"""
        await repository.create(sample_event)
        with pytest.raises(EventAlreadyExistsError) as exc_info:
            await repository.create(sample_event)
        assert exc_info.value.event_id == sample_event.event_id

    async def test_update_status_existing_event(self, populated_repository: InMemoryEventRepository):
        """Should successfully update event status"""
        event = await populated_repository.update_status(1, EventStatus.FINISHED_WIN)
        assert event.status == EventStatus.FINISHED_WIN
        # Verify persistence
        retrieved_event = await populated_repository.get_by_id(1)
        assert retrieved_event.status == EventStatus.FINISHED_WIN

    async def test_update_status_non_existing_event(self, repository: InMemoryEventRepository):
        """Should raise EventNotFoundError when updating non-existing event"""
        with pytest.raises(EventNotFoundError) as exc_info:
            await repository.update_status(999, EventStatus.FINISHED_WIN)
        assert exc_info.value.event_id == 999

    async def test_exists_existing_event(self, populated_repository: InMemoryEventRepository):
        """Should return True for existing event"""
        assert await populated_repository.exists(1)

    async def test_exists_non_existing_event(self, repository: InMemoryEventRepository):
        """Should return False for non-existing event"""
        assert not await repository.exists(999)

    async def test_clear_repository(self, populated_repository: InMemoryEventRepository):
        """Should remove all events from repository"""
        assert len(await populated_repository.get_all()) > 0
        await populated_repository.clear()
        assert len(await populated_repository.get_all()) == 0

    async def test_coefficient_validation(self, repository: InMemoryEventRepository, future_timestamp: int):
        """Should enforce coefficient validation rules"""
        with pytest.raises(ValueError):
            event = Event(
                event_id=1,
                coefficient=Decimal("0"),  # Invalid: must be > 0
                deadline=future_timestamp,
                status=EventStatus.NEW
            )
            await repository.create(event)

    async def test_deadline_validation(self, repository: InMemoryEventRepository, expired_timestamp: int):
        """Should enforce deadline validation rules"""
        with pytest.raises(InvalidEventDeadlineError):
            event = Event(
                event_id=1,
                coefficient=Decimal("1.50"),
                deadline=expired_timestamp,  # Invalid: must be in future
                status=EventStatus.NEW
            )
            await repository.create(event)