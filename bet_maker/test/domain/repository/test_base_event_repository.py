import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from unittest.mock import AsyncMock, patch

from src.domain.entity import Event
from src.domain.vo import EventStatus
from src.domain.repository import BaseEventRepository
from src.exception import EventNotFoundError

pytestmark = pytest.mark.asyncio


class MockEventRepository(BaseEventRepository):
    def __init__(self, events: List[Dict[str, Any]] = None):
        self.events = {}
        if events:
            for event_data in events:
                event = Event.model_validate(event_data)
                self.events[event.event_id] = event
        self.get_all_mock = AsyncMock(side_effect=self._get_all)
        self.get_by_id_mock = AsyncMock(side_effect=self._get_by_id)
        self.get_active_events_mock = AsyncMock(side_effect=self._get_active_events)
        self.filter_events_mock = AsyncMock(side_effect=self._filter_events)
        self.exists_mock = AsyncMock(side_effect=self._exists)

    async def get_all(self) -> List[Event]:
        return await self.get_all_mock()

    async def _get_all(self) -> List[Event]:
        return list(self.events.values())

    async def get_by_id(self, event_id: Union[int, str]) -> Event:
        return await self.get_by_id_mock(event_id)

    async def _get_by_id(self, event_id: Union[int, str]) -> Event:
        if event_id not in self.events:
            raise EventNotFoundError(event_id)
        return self.events[event_id]

    async def get_active_events(self) -> List[Event]:
        return await self.get_active_events_mock()

    async def _get_active_events(self) -> List[Event]:
        current_time = int(datetime.now().timestamp())
        return [
            event for event in self.events.values()
            if event.status.is_active and event.deadline > current_time
        ]

    async def filter_events(self, 
                           status: Optional[EventStatus] = None,
                           before_deadline: Optional[datetime] = None,
                           after_deadline: Optional[datetime] = None) -> List[Event]:
        return await self.filter_events_mock(status, before_deadline, after_deadline)

    async def _filter_events(self, 
                            status: Optional[EventStatus] = None,
                            before_deadline: Optional[datetime] = None,
                            after_deadline: Optional[datetime] = None) -> List[Event]:
        result = list(self.events.values())
        if status:
            result = [event for event in result if event.status == status]
        if before_deadline:
            before_timestamp = int(before_deadline.timestamp())
            result = [event for event in result if event.deadline < before_timestamp]
        if after_deadline:
            after_timestamp = int(after_deadline.timestamp())
            result = [event for event in result if event.deadline > after_timestamp]
        return result

    async def exists(self, event_id: Union[int, str]) -> bool:
        return await self.exists_mock(event_id)

    async def _exists(self, event_id: Union[int, str]) -> bool:
        return event_id in self.events


@pytest.fixture
def sample_events():
    now = datetime.now()
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    return [
        {
            "event_id": 1,
            "coefficient": Decimal("1.50"),
            "deadline": int(future.timestamp()),
            "status": EventStatus.NEW
        },
        {
            "event_id": 2,
            "coefficient": Decimal("2.00"),
            "deadline": int(past.timestamp()),
            "status": EventStatus.NEW
        },
        {
            "event_id": 3,
            "coefficient": Decimal("3.00"),
            "deadline": int(future.timestamp()),
            "status": EventStatus.FINISHED_WIN
        },
        {
            "event_id": 4,
            "coefficient": Decimal("4.00"),
            "deadline": int(future.timestamp()),
            "status": EventStatus.FINISHED_LOSE
        }
    ]


@pytest.fixture
def mock_repository(sample_events):
    return MockEventRepository(sample_events)


class TestBaseEventRepository:
    async def test_get_all(self, mock_repository, sample_events):
        events = await mock_repository.get_all()
        assert len(events) == len(sample_events)
        assert mock_repository.get_all_mock.called

    async def test_get_by_id_existing(self, mock_repository):
        event = await mock_repository.get_by_id(1)
        assert event.event_id == 1
        assert event.coefficient == Decimal("1.50")
        assert mock_repository.get_by_id_mock.called

    async def test_get_by_id_nonexistent(self, mock_repository):
        with pytest.raises(EventNotFoundError) as exc_info:
            await mock_repository.get_by_id(999)
        assert "999" in str(exc_info.value)
        assert mock_repository.get_by_id_mock.called

    async def test_get_active_events(self, mock_repository):
        active_events = await mock_repository.get_active_events()
        assert len(active_events) == 1
        assert active_events[0].event_id == 1
        assert mock_repository.get_active_events_mock.called

    async def test_filter_events_by_status(self, mock_repository):
        new_events = await mock_repository.filter_events(status=EventStatus.NEW)
        finished_win_events = await mock_repository.filter_events(status=EventStatus.FINISHED_WIN)
        assert len(new_events) == 2
        assert all(e.status == EventStatus.NEW for e in new_events)
        assert len(finished_win_events) == 1
        assert finished_win_events[0].event_id == 3

    async def test_filter_events_by_deadline(self, mock_repository):
        now = datetime.now()
        future_events = await mock_repository.filter_events(after_deadline=now)
        past_events = await mock_repository.filter_events(before_deadline=now)
        assert len(future_events) == 3
        assert all(e.event_id in [1, 3, 4] for e in future_events)
        assert len(past_events) == 1
        assert past_events[0].event_id == 2
        assert mock_repository.filter_events_mock.call_count == 2

    async def test_exists(self, mock_repository):
        assert await mock_repository.exists(1) is True
        assert await mock_repository.exists(999) is False
        assert mock_repository.exists_mock.call_count == 2