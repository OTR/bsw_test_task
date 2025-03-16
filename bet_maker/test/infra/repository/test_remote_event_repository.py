import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from decimal import Decimal

from httpx import HTTPStatusError, Response

from src.domain.entity import Event
from src.domain.vo import EventStatus
from src.infra.http.http_client import HTTPClient
from src.infra.repository import RemoteEventRepository
from src.exception import EventNotFoundError, EventRepositoryConnectionError

pytestmark = pytest.mark.asyncio


class TestRemoteEventRepository:

    @pytest.fixture
    def mock_http_client(self):
        client = MagicMock(spec=HTTPClient)
        client.get = AsyncMock()
        client.get_json = AsyncMock()
        client.get_model = AsyncMock()
        client.get_model_list = AsyncMock()
        return client

    @pytest.fixture
    def repository(self, mock_http_client):
        return RemoteEventRepository(http_client=mock_http_client)

    @pytest.fixture
    def sample_events(self):
        now = datetime.now()
        now_timestamp = int(now.timestamp())
        
        return [
            Event(
                event_id=1,
                coefficient=Decimal("1.50"),
                deadline=now_timestamp + 86400,  # 1 day from now
                status=EventStatus.NEW
            ),
            Event(
                event_id=2,
                coefficient=Decimal("1.75"),
                deadline=now_timestamp - 86400,  # 1 day ago
                status=EventStatus.FINISHED_WIN
            ),
            Event(
                event_id=3,
                coefficient=Decimal("1.25"),
                deadline=now_timestamp + 172800,  # 2 days from now
                status=EventStatus.NEW
            )
        ]

    async def test_get_all_success(self, repository, mock_http_client, sample_events):
        mock_http_client.get_model_list.return_value = sample_events
        
        events = await repository.get_all()
        
        assert events == sample_events
        mock_http_client.get_model_list.assert_called_once_with("/api/v1/events", Event)

    async def test_get_all_error(self, repository, mock_http_client):
        mock_http_client.get_model_list.side_effect = Exception("Connection error")
        
        with pytest.raises(EventRepositoryConnectionError) as exc_info:
            await repository.get_all()
        
        assert "Connection error" in str(exc_info.value)
        mock_http_client.get_model_list.assert_called_once()

    async def test_get_by_id_success(self, repository, mock_http_client, sample_events):
        mock_http_client.get_model.return_value = sample_events[0]
        
        event = await repository.get_by_id(1)
        
        assert event == sample_events[0]
        mock_http_client.get_model.assert_called_once_with("/api/v1/event/1", Event)

    async def test_get_by_id_not_found(self, repository, mock_http_client):
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 404
        
        http_error = HTTPStatusError("Event not found", request=MagicMock(), response=mock_response)
        
        mock_http_client.get_model.side_effect = http_error
        
        with pytest.raises(EventNotFoundError) as exc_info:
            await repository.get_by_id(999)
        
        assert "999" in str(exc_info.value)
        mock_http_client.get_model.assert_called_once()

    async def test_get_by_id_other_error(self, repository, mock_http_client):
        mock_http_client.get_model.side_effect = Exception("Unexpected error")
        
        with pytest.raises(EventRepositoryConnectionError) as exc_info:
            await repository.get_by_id(1)
        
        assert "Unexpected error" in str(exc_info.value)
        mock_http_client.get_model.assert_called_once()

    async def test_get_active_events(self, repository, mock_http_client, sample_events):
        mock_http_client.get_model_list.return_value = sample_events
        
        active_events = await repository.get_active_events()
        
        now_timestamp = int(datetime.now().timestamp())
        expected_events = [event for event in sample_events 
                           if event.status == EventStatus.NEW and event.deadline > now_timestamp]
        
        assert len(active_events) == len(expected_events)
        assert all(event in expected_events for event in active_events)
        mock_http_client.get_model_list.assert_called_once()

    async def test_filter_events_by_status(self, repository, mock_http_client, sample_events):
        mock_http_client.get_model_list.return_value = sample_events
        
        filtered_events = await repository.filter_events(status=EventStatus.NEW)
        
        expected_events = [event for event in sample_events if event.status == EventStatus.NEW]
        
        assert len(filtered_events) == len(expected_events)
        assert all(event in expected_events for event in filtered_events)
        mock_http_client.get_model_list.assert_called_once()

    async def test_filter_events_by_deadline(self, repository, mock_http_client, sample_events):
        mock_http_client.get_model_list.return_value = sample_events
        now = datetime.now()
        now_timestamp = int(now.timestamp())
        
        filtered_events = await repository.filter_events(deadline_after=now)
        
        expected_events = [event for event in sample_events if event.deadline > now_timestamp]
        
        assert len(filtered_events) == len(expected_events)
        assert all(event in expected_events for event in filtered_events)
        mock_http_client.get_model_list.assert_called_once()

    async def test_exists_true(self, repository, mock_http_client, sample_events):
        mock_http_client.get_model.return_value = sample_events[0]
        
        exists = await repository.exists(1)
        
        assert exists is True
        mock_http_client.get_model.assert_called_once()

    async def test_exists_false(self, repository, mock_http_client):
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 404
        
        http_error = HTTPStatusError("Event not found", request=MagicMock(), response=mock_response)
        
        mock_http_client.get_model.side_effect = http_error
        
        exists = await repository.exists(999)
        
        assert exists is False
        mock_http_client.get_model.assert_called_once()
