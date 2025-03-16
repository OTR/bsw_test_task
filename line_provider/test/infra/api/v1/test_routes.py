import json
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.domain.entity import Event, CreateEventRequest
from src.domain.vo import EventStatus
from src.application.service import EventService
from src.exception import EventNotFoundError, EventAlreadyExistsError
from src.di.container import get_event_service


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

class CustomTestClient(TestClient):
    def put(self, url, *, json=None, **kwargs):
        if json is not None:
            encoded_json = json_dumps_with_decimal(json)
            kwargs.setdefault("content", encoded_json)
            kwargs.setdefault("headers", {}).setdefault("content-type", "application/json")
            return self.request("PUT", url, **kwargs)
        return super().put(url, json=json, **kwargs)
    
    def post(self, url, *, json=None, **kwargs):
        if json is not None:
            encoded_json = json_dumps_with_decimal(json)
            kwargs.setdefault("content", encoded_json)
            kwargs.setdefault("headers", {}).setdefault("content-type", "application/json")
            return self.request("POST", url, **kwargs)
        return super().post(url, json=json, **kwargs)

def json_dumps_with_decimal(obj):
    return json.dumps(obj, cls=DecimalEncoder)

@pytest.fixture
def mock_event_service():
    service = AsyncMock(spec=EventService)
    service.get_all_events = AsyncMock(return_value=[])
    service.get_active_events = AsyncMock(return_value=[])
    service.get_event = AsyncMock()
    service.create_event = AsyncMock()
    service.update_event = AsyncMock()
    service.event_exists = AsyncMock(return_value=False)
    service.finish_event = AsyncMock()
    return service

@pytest.fixture
def client():
    from main import create_app
    app = create_app()
    return CustomTestClient(app)

class TestCreateEvent:
    @pytest.fixture
    def valid_payload(self):
        return {
            "event_id": 123,
            "coefficient": Decimal('1.45'),
            "deadline": 1743000000,
            "status": "NEW"
        }
    
    @pytest.fixture
    def invalid_coefficient_payload(self):
        return {
            "event_id": 123,
            "coefficient": 1,
            "deadline": 1743000000,
            "status": "NEW"
        }
    
    @pytest.fixture
    def invalid_deadline_payload(self):
        return {
            "event_id": 123,
            "coefficient": Decimal('1.45'),
            "deadline": 1600000000,
            "status": "NEW"
        }
    
    def test_create_event_success(self, client, mock_event_service, valid_payload):
        mock_event_service.event_exists.return_value = False
        mock_event_service.create_event.return_value = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.NEW
        )
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.post("/api/v1/event", json=valid_payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"success": True, "event_id": 123}
        mock_event_service.event_exists.assert_called_once_with(123)
        mock_event_service.create_event.assert_called_once()
    
    def test_create_event_already_exists(self, client, mock_event_service, valid_payload):
        event_id = valid_payload["event_id"]
        mock_event_service.event_exists.return_value = True
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.post("/api/v1/event", json=valid_payload)
        assert response.status_code == status.HTTP_409_CONFLICT
        error_data = response.json()
        assert "already exists" in error_data["error"]["message"].lower()
        mock_event_service.event_exists.assert_called_once_with(event_id)
        mock_event_service.create_event.assert_not_called()
    
    def test_create_event_invalid_coefficient(self, client, mock_event_service, invalid_coefficient_payload):
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.post("/api/v1/event", json=invalid_coefficient_payload)
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
        error_data = response.json()
        assert "coefficient" in str(error_data).lower()
        mock_event_service.event_exists.assert_not_called()
        mock_event_service.create_event.assert_not_called()

class TestUpdateEvent:
    @pytest.fixture
    def valid_update_payload(self):
        return {
            "event_id": 123,
            "coefficient": Decimal('2.50'),
            "deadline": 1743000000,
            "status": "NEW"
        }
    
    def test_update_event_success(self, client, mock_event_service, valid_update_payload):
        event_id = valid_update_payload["event_id"]
        mock_event_service.event_exists.return_value = True
        coefficient = valid_update_payload["coefficient"]
        deadline = valid_update_payload["deadline"]
        status_value = valid_update_payload["status"]
        mock_event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=deadline,
            status=EventStatus(status_value)
        )
        mock_event_service.update_event.return_value = mock_event
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.put(f"/api/v1/event/{event_id}", json=valid_update_payload)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["event_id"] == event_id
        mock_event_service.event_exists.assert_called_once_with(event_id)
        mock_event_service.update_event.assert_called_once()
    
    def test_update_event_not_found(self, client, mock_event_service, valid_update_payload):
        event_id = valid_update_payload["event_id"]
        mock_event_service.event_exists.return_value = False
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.put(f"/api/v1/event/{event_id}", json=valid_update_payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()
        mock_event_service.event_exists.assert_called_once_with(event_id)
        mock_event_service.update_event.assert_not_called()
    
    def test_update_event_id_mismatch(self, client, mock_event_service, valid_update_payload):
        mismatched_id = 999
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.put(f"/api/v1/event/{mismatched_id}", json=valid_update_payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "match" in str(error_data).lower()
        mock_event_service.event_exists.assert_not_called()
        mock_event_service.update_event.assert_not_called()

class TestGetEventById:
    def test_get_event_success(self, client, mock_event_service):
        event_id = 123
        mock_event_service.get_event.return_value = Event(
            event_id=event_id,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.NEW
        )
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.get(f"/api/v1/event/{event_id}")
        assert response.status_code == status.HTTP_200_OK
        event_data = response.json()
        assert event_data["event_id"] == event_id
        assert event_data["coefficient"] == "1.45"
        assert event_data["status"] == "NEW"
        mock_event_service.get_event.assert_called_once_with(event_id)
    
    def test_get_event_not_found(self, client, mock_event_service):
        event_id = 999
        mock_event_service.get_event.side_effect = EventNotFoundError(event_id)
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.get(f"/api/v1/event/{event_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "not found" in error_data["error"]["message"].lower()
        mock_event_service.get_event.assert_called_once_with(event_id)

class TestGetEvents:
    def test_get_all_events(self, client, mock_event_service):
        mock_event_service.get_all_events.return_value = [
            Event(event_id=123, coefficient=Decimal('1.45'), deadline=1743000000, status=EventStatus.NEW),
            Event(event_id=456, coefficient=Decimal('2.10'), deadline=1744000000, status=EventStatus.NEW),
            Event(event_id=789, coefficient=Decimal('3.25'), deadline=1745000000, status=EventStatus.FINISHED_WIN)
        ]
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.get("/api/v1/events")
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 3
        event_ids = [event["event_id"] for event in events]
        assert 123 in event_ids
        assert 456 in event_ids
        assert 789 in event_ids
        mock_event_service.get_all_events.assert_called_once()
    
    def test_get_all_events_empty(self, client, mock_event_service):
        mock_event_service.get_all_events.return_value = []
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.get("/api/v1/events")
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0
        assert isinstance(events, list)
        mock_event_service.get_all_events.assert_called_once()

class TestGetActiveEvents:
    def test_get_active_events(self, client, mock_event_service):
        active_events = [
            Event(event_id=123, coefficient=Decimal('1.45'), deadline=1743000000, status=EventStatus.NEW),
            Event(event_id=456, coefficient=Decimal('2.10'), deadline=1744000000, status=EventStatus.NEW)
        ]
        mock_event_service.get_active_events.return_value = active_events
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.get("/api/v1/events/active")
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == len(active_events)
        for event in events:
            assert event["status"] == "NEW"
            assert event["is_active"] is True
        mock_event_service.get_active_events.assert_called_once()
    
    def test_get_active_events_empty(self, client, mock_event_service):
        mock_event_service.get_active_events.return_value = []
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        response = client.get("/api/v1/events/active")
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0
        assert isinstance(events, list)
        mock_event_service.get_active_events.assert_called_once()

class TestFinishEvent:
    @pytest.mark.asyncio
    async def test_finish_event_win(self, mock_event_service):
        mock_event_service.get_event.return_value = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.NEW
        )
        finished_event = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.FINISHED_WIN
        )
        mock_event_service.finish_event.return_value = finished_event
        result = await mock_event_service.finish_event(123, True)
        assert result.status == EventStatus.FINISHED_WIN
        assert result.event_id == 123
        mock_event_service.finish_event.assert_called_once_with(123, True)
    
    @pytest.mark.asyncio
    async def test_finish_event_lose(self, mock_event_service):
        mock_event_service.get_event.return_value = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.NEW
        )
        finished_event = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.FINISHED_LOSE
        )
        mock_event_service.finish_event.return_value = finished_event
        result = await mock_event_service.finish_event(123, False)
        assert result.status == EventStatus.FINISHED_LOSE
        assert result.event_id == 123
        mock_event_service.finish_event.assert_called_once_with(123, False)
    
    @pytest.mark.asyncio
    async def test_finish_already_finished_event(self, mock_event_service):
        event_id = 123
        mock_event_service.get_event.return_value = Event(
            event_id=event_id,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.FINISHED_WIN
        )
        error_msg = f"Event {event_id} is already finished"
        mock_event_service.finish_event.side_effect = ValueError(error_msg)
        with pytest.raises(ValueError, match=error_msg):
            await mock_event_service.finish_event(event_id, True)
        mock_event_service.finish_event.assert_called_once_with(event_id, True)
    
    @pytest.mark.asyncio
    async def test_finish_nonexistent_event(self, mock_event_service):
        event_id = 999
        mock_event_service.get_event.side_effect = EventNotFoundError(event_id)
        mock_event_service.finish_event.side_effect = EventNotFoundError(event_id)
        with pytest.raises(EventNotFoundError, match=f".*{event_id}.*"):
            await mock_event_service.finish_event(event_id, True)
        mock_event_service.finish_event.assert_called_once_with(event_id, True)

class TestCreateEventRequestValidation:
    def test_coefficient_valid_decimal_places(self):
        valid_values = ["1.45", "2.00", "123.45"]
        for val in valid_values:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal(val),
                deadline=1743000000,
                status=EventStatus.NEW
            )
    
    def test_coefficient_invalid_integer(self):
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("5"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        assert "decimal places" in str(excinfo.value)
    
    def test_coefficient_invalid_one_decimal_place(self):
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("5.5"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        assert "decimal places" in str(excinfo.value)
    
    def test_coefficient_invalid_three_decimal_places(self):
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("5.555"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        assert "decimal places" in str(excinfo.value)
    
    def test_negative_event_id_rejected(self):
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=-1,
                coefficient=Decimal("1.45"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        assert "event_id" in str(excinfo.value).lower()
    
    def test_negative_deadline_rejected(self):
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("1.45"),
                deadline=-1,
                status=EventStatus.NEW
            )
        assert "deadline" in str(excinfo.value).lower()
    
    def test_to_domain_conversion(self):
        dto = CreateEventRequest(
            event_id=123,
            coefficient=Decimal("1.45"),
            deadline=1743000000,
            status=EventStatus.NEW
        )
        event = dto.to_domain()
        assert event.event_id == 123
        assert event.coefficient == Decimal("1.45")
        assert event.deadline == 1743000000
        assert event.status == EventStatus.NEW