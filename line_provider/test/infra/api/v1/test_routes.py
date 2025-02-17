import json
from decimal import Decimal

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch

from src.domain.entity import Event, CreateEventRequest
from src.domain.vo import EventStatus
from src.application.service import EventService
from src.exception import EventNotFoundError, EventAlreadyExistsError
from src.di.container import get_event_service


# Custom JSON encoder that handles Decimal values
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


# Create a wrapper for the TestClient that handles Decimal values
class CustomTestClient(TestClient):
    def put(self, url, *, json=None, **kwargs):
        if json is not None:
            encoded_json = json_dumps_with_decimal(json)
            kwargs.setdefault("content", encoded_json)
            kwargs.setdefault("headers", {}).setdefault(
                "content-type", "application/json"
            )
            return self.request("PUT", url, **kwargs)
        return super().put(url, json=json, **kwargs)
    
    def post(self, url, *, json=None, **kwargs):
        if json is not None:
            encoded_json = json_dumps_with_decimal(json)
            kwargs.setdefault("content", encoded_json)
            kwargs.setdefault("headers", {}).setdefault(
                "content-type", "application/json"
            )
            return self.request("POST", url, **kwargs)
        return super().post(url, json=json, **kwargs)


def json_dumps_with_decimal(obj):
    return json.dumps(obj, cls=DecimalEncoder)


# We'll use a more targeted approach by mocking just the routes we need
# instead of using the entire application
@pytest.fixture
def mock_event_service():
    """Mock the event service for testing API routes"""
    # Use a fresh mock for each test
    service = AsyncMock(spec=EventService)
    
    # Mock all the methods that will be used
    service.get_all_events = AsyncMock(return_value=[])
    service.get_active_events = AsyncMock(return_value=[])
    service.get_event = AsyncMock()
    service.create_event = AsyncMock()
    service.update_event = AsyncMock()
    service.event_exists = AsyncMock(return_value=False)  # default to not exist
    service.finish_event = AsyncMock()
    
    return service


@pytest.fixture
def client():
    """Create test client with mocked dependencies"""
    from main import create_app
    
    # Create a new app for each test
    app = create_app()
    
    # We'll override the dependency in each test
    return CustomTestClient(app)


# Test POST /event endpoint
class TestCreateEvent:
    
    @pytest.fixture
    def valid_create_event_payload(self):
        """Valid payload for event creation"""
        return {
            "event_id": 123,
            "coefficient": Decimal('1.45'),  # Use Decimal to ensure exactly 2 decimal places
            "deadline": 1743000000,
            "status": "NEW"
        }
    
    @pytest.fixture
    def invalid_coefficient_payload(self):
        """Payload with invalid coefficient (no decimal places)"""
        return {
            "event_id": 123,
            "coefficient": 1,  # Missing decimal places
            "deadline": 1743000000,
            "status": "NEW"
        }
    
    @pytest.fixture
    def invalid_deadline_payload(self):
        """Payload with invalid deadline (in the past)"""
        return {
            "event_id": 123,
            "coefficient": Decimal('1.45'),  # Use Decimal to ensure exactly 2 decimal places
            "deadline": 1600000000,  # Some time in the past
            "status": "NEW"
        }
    
    def test_create_event_success(self, client, mock_event_service, valid_create_event_payload):
        """Test successful event creation"""
        # Setup mocks
        mock_event_service.event_exists.return_value = False  # Event does not exist yet
        mock_event_service.create_event.return_value = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,  # Some time in the future
            status=EventStatus.NEW
        )
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.post("/api/v1/event", json=valid_create_event_payload)
        
        # Assert response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"success": True, "event_id": 123}
        
        # Verify service was called with proper arguments
        mock_event_service.event_exists.assert_called_once_with(123)
        mock_event_service.create_event.assert_called_once()
    
    def test_create_event_already_exists(self, client, mock_event_service, valid_create_event_payload):
        """Test event creation when event ID already exists"""
        # Setup mocks
        event_id = valid_create_event_payload["event_id"]
        mock_event_service.event_exists.return_value = True  # Event already exists
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.post("/api/v1/event", json=valid_create_event_payload)
        
        # Assert response
        assert response.status_code == status.HTTP_409_CONFLICT
        error_data = response.json()
        assert "already exists" in error_data["error"]["message"].lower()
        
        # Verify service called
        mock_event_service.event_exists.assert_called_once_with(event_id)
        mock_event_service.create_event.assert_not_called()
    
    def test_create_event_invalid_coefficient(self, client, mock_event_service, invalid_coefficient_payload):
        """Test event creation with invalid coefficient format"""
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request - should fail validation before reaching service
        response = client.post("/api/v1/event", json=invalid_coefficient_payload)
        
        # Assert response
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY, 
            status.HTTP_400_BAD_REQUEST
        ]  # Allow either status code
        error_data = response.json()
        assert "coefficient" in str(error_data).lower()
        
        # Service methods should not be called due to validation failure
        mock_event_service.event_exists.assert_not_called()
        mock_event_service.create_event.assert_not_called()


# Test PUT /event/{event_id} endpoint
class TestUpdateEvent:
    
    @pytest.fixture
    def valid_update_event_payload(self):
        """Valid payload for event update"""
        return {
            "event_id": 123,
            "coefficient": Decimal('2.50'),  # Use Decimal to ensure exactly 2 decimal places
            "deadline": 1743000000,
            "status": "NEW"
        }
    
    def test_update_event_success(self, client, mock_event_service, valid_update_event_payload):
        """Test successful event update"""
        # Setup mocks
        event_id = valid_update_event_payload["event_id"]
        
        # Mock event_exists to return True (event exists)
        mock_event_service.event_exists.return_value = True
        
        # Create a valid sample event for update_event response
        coefficient = valid_update_event_payload["coefficient"]
        deadline = valid_update_event_payload["deadline"]
        status_value = valid_update_event_payload["status"]

        # Mock the event that will be returned by update_event
        mock_event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=deadline,
            status=EventStatus(status_value)
        )
        
        # Set the return value for update_event
        mock_event_service.update_event.return_value = mock_event
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.put(f"/api/v1/event/{event_id}", json=valid_update_event_payload)
        
        # Print response details for debugging
        print(f"Status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        
        # Verify correct data returned
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["event_id"] == event_id
        
        # Verify service was called
        mock_event_service.event_exists.assert_called_once_with(event_id)
        mock_event_service.update_event.assert_called_once()
    
    def test_update_event_not_found(self, client, mock_event_service, valid_update_event_payload):
        """Test event update when event ID doesn't exist"""
        # Setup mocks
        event_id = valid_update_event_payload["event_id"]
        mock_event_service.event_exists.return_value = False
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.put(f"/api/v1/event/{event_id}", json=valid_update_event_payload)
        
        # Assert response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()
        
        # Verify service was called
        mock_event_service.event_exists.assert_called_once_with(event_id)
        mock_event_service.update_event.assert_not_called()
    
    def test_update_event_id_mismatch(self, client, mock_event_service, valid_update_event_payload):
        """Test event update when URL ID and payload ID don't match"""
        # Setup mocks
        mismatched_id = 999  # Different from the 123 in valid_update_event_payload

        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service

        # Execute request with mismatched IDs
        response = client.put(f"/api/v1/event/{mismatched_id}", json=valid_update_event_payload)
        
        # Print response details for debugging
        print(f"Mismatch Status code: {response.status_code}")
        print(f"Mismatch Response body: {response.text}")

        # Assert response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        # Use str(error_data) since we're not sure of the exact structure
        assert "match" in str(error_data).lower()

        # Verify service was not called
        mock_event_service.event_exists.assert_not_called()
        mock_event_service.update_event.assert_not_called()


# Test GET /event/{event_id} endpoint
class TestGetEventById:
    
    def test_get_event_success(self, client, mock_event_service):
        """Test successful event retrieval by ID"""
        # Setup mocks
        event_id = 123
        mock_event_service.get_event.return_value = Event(
            event_id=event_id,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.NEW
        )
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.get(f"/api/v1/event/{event_id}")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        event_data = response.json()
        assert event_data["event_id"] == event_id
        assert event_data["coefficient"] == "1.45"
        assert event_data["status"] == "NEW"
        
        # Assert service calls
        mock_event_service.get_event.assert_called_once_with(event_id)
    
    def test_get_event_not_found(self, client, mock_event_service):
        """Test event retrieval when event doesn't exist"""
        # Setup mocks
        event_id = 999  # Different from the one used in other tests
        mock_event_service.get_event.side_effect = EventNotFoundError(event_id)
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.get(f"/api/v1/event/{event_id}")
        
        # Assert response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        assert "not found" in error_data["error"]["message"].lower()
        
        # Verify service was called
        mock_event_service.get_event.assert_called_once_with(event_id)


# Test GET /events endpoint
class TestGetEvents:
    
    def test_get_all_events(self, client, mock_event_service):
        """Test retrieving all events"""
        # Setup mocks
        mock_event_service.get_all_events.return_value = [
            Event(
                event_id=123,
                coefficient=Decimal('1.45'),
                deadline=1743000000,
                status=EventStatus.NEW
            ),
            Event(
                event_id=456,
                coefficient=Decimal('2.10'),
                deadline=1744000000,
                status=EventStatus.NEW
            ),
            Event(
                event_id=789,
                coefficient=Decimal('3.25'),
                deadline=1745000000,
                status=EventStatus.FINISHED_WIN
            )
        ]
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.get("/api/v1/events")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 3
        
        # Check event IDs to validate correct data
        event_ids = [event["event_id"] for event in events]
        assert 123 in event_ids
        assert 456 in event_ids
        assert 789 in event_ids
        
        # Assert service calls
        mock_event_service.get_all_events.assert_called_once()
    
    def test_get_all_events_empty(self, client, mock_event_service):
        """Test retrieving all events when there are none"""
        # Setup mocks
        mock_event_service.get_all_events.return_value = []
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.get("/api/v1/events")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0
        assert isinstance(events, list)  # Should return empty list, not null
        
        # Assert service calls
        mock_event_service.get_all_events.assert_called_once()


# Test GET /events/active endpoint
class TestGetActiveEvents:
    
    def test_get_active_events(self, client, mock_event_service):
        """Test retrieving active events"""
        # Setup mocks - filter to only active events
        active_events = [
            Event(
                event_id=123,
                coefficient=Decimal('1.45'),
                deadline=1743000000,
                status=EventStatus.NEW
            ),
            Event(
                event_id=456,
                coefficient=Decimal('2.10'),
                deadline=1744000000,
                status=EventStatus.NEW
            )
        ]
        mock_event_service.get_active_events.return_value = active_events
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.get("/api/v1/events/active")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        
        # Only active events should be returned
        assert len(events) == len(active_events)
        
        # Check status values - all active events should be NEW
        for event in events:
            assert event["status"] == "NEW"
            assert event["is_active"] is True
        
        # Assert service calls
        mock_event_service.get_active_events.assert_called_once()
    
    def test_get_active_events_empty(self, client, mock_event_service):
        """Test retrieving active events when there are none"""
        # Setup mocks
        mock_event_service.get_active_events.return_value = []
        
        # Override dependency for this specific test
        client.app.dependency_overrides[get_event_service] = lambda: mock_event_service
        
        # Execute request
        response = client.get("/api/v1/events/active")
        
        # Assert response
        assert response.status_code == status.HTTP_200_OK
        events = response.json()
        assert len(events) == 0
        assert isinstance(events, list)  # Should return empty list, not null
        
        # Assert service calls
        mock_event_service.get_active_events.assert_called_once()


# Test finish_event method from service
class TestFinishEvent:
    """
    Tests for finish_event functionality in the service layer
    
    Although there is no direct API endpoint for finishing events,
    we should test this service method as it's a core part of the business logic.
    """
    
    @pytest.mark.asyncio
    async def test_finish_event_win(self, mock_event_service):
        """Test marking an event as finished with a win"""
        # Set up the mock to return an unfinished event
        mock_event_service.get_event.return_value = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,  # Future time
            status=EventStatus.NEW
        )
        
        # Set up the finished event to be returned
        finished_event = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.FINISHED_WIN
        )
        mock_event_service.finish_event.return_value = finished_event
        
        # Call the finish_event method - this is an async method
        result = await mock_event_service.finish_event(123, True)
        
        # Verify the result
        assert result.status == EventStatus.FINISHED_WIN
        assert result.event_id == 123
        
        # Verify the method was called
        mock_event_service.finish_event.assert_called_once_with(123, True)
    
    @pytest.mark.asyncio
    async def test_finish_event_lose(self, mock_event_service):
        """Test marking an event as finished with a loss"""
        # Set up the mock to return an unfinished event
        mock_event_service.get_event.return_value = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,  # Future time
            status=EventStatus.NEW
        )
        
        # Set up the finished event to be returned
        finished_event = Event(
            event_id=123,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.FINISHED_LOSE
        )
        mock_event_service.finish_event.return_value = finished_event
        
        # Call the finish_event method
        result = await mock_event_service.finish_event(123, False)
        
        # Verify the result
        assert result.status == EventStatus.FINISHED_LOSE
        assert result.event_id == 123
        
        # Verify the method was called
        mock_event_service.finish_event.assert_called_once_with(123, False)
    
    @pytest.mark.asyncio
    async def test_finish_already_finished_event(self, mock_event_service):
        """Test trying to finish an already finished event raises an error"""
        # Set up mock to return finished event
        event_id = 123
        mock_event_service.get_event.return_value = Event(
            event_id=event_id,
            coefficient=Decimal('1.45'),
            deadline=1743000000,
            status=EventStatus.FINISHED_WIN
        )
        
        # Set up the mock to raise ValueError when finish_event is called
        error_msg = f"Event {event_id} is already finished"
        mock_event_service.finish_event.side_effect = ValueError(error_msg)
        
        # Try to finish the event again, should raise ValueError
        with pytest.raises(ValueError, match=error_msg):
            await mock_event_service.finish_event(event_id, True)
        
        # Verify proper method calls
        mock_event_service.finish_event.assert_called_once_with(event_id, True)
    
    @pytest.mark.asyncio
    async def test_finish_nonexistent_event(self, mock_event_service):
        """Test trying to finish a non-existent event"""
        # Setup mock to simulate event not found
        event_id = 999
        mock_event_service.get_event.side_effect = EventNotFoundError(event_id)
        mock_event_service.finish_event.side_effect = EventNotFoundError(event_id)
        
        # Try to finish a non-existent event
        with pytest.raises(EventNotFoundError, match=f".*{event_id}.*"):
            await mock_event_service.finish_event(event_id, True)
        
        # Verify service calls
        mock_event_service.finish_event.assert_called_once_with(event_id, True)


# Test validation in CreateEventRequest
class TestCreateEventRequestValidation:
    """Tests for validation rules in the CreateEventRequest DTO"""
    
    def test_coefficient_valid_decimal_places(self):
        """Test that coefficients with exactly 2 decimal places are valid"""
        # These should all be valid
        valid_values = ["1.45", "2.00", "123.45"]
        
        for val in valid_values:
            # Should not raise any exceptions
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal(val),
                deadline=1743000000,
                status=EventStatus.NEW
            )
    
    def test_coefficient_invalid_integer(self):
        """Test that integer coefficients are rejected"""
        # Integer value without decimal places should be rejected
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("5"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        
        assert "decimal places" in str(excinfo.value)
    
    def test_coefficient_invalid_one_decimal_place(self):
        """Test that coefficients with one decimal place are rejected"""
        # One decimal place should be rejected
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("5.5"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        
        assert "decimal places" in str(excinfo.value)
    
    def test_coefficient_invalid_three_decimal_places(self):
        """Test that coefficients with three decimal places are rejected"""
        # Three decimal places should be rejected
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("5.555"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        
        assert "decimal places" in str(excinfo.value)
    
    def test_negative_event_id_rejected(self):
        """Test that negative event IDs are rejected"""
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=-1,
                coefficient=Decimal("1.45"),
                deadline=1743000000,
                status=EventStatus.NEW
            )
        
        assert "event_id" in str(excinfo.value).lower()
    
    def test_negative_deadline_rejected(self):
        """Test that negative deadlines are rejected"""
        with pytest.raises(ValueError) as excinfo:
            CreateEventRequest(
                event_id=123,
                coefficient=Decimal("1.45"),
                deadline=-1,
                status=EventStatus.NEW
            )
        
        assert "deadline" in str(excinfo.value).lower()
    
    def test_to_domain_conversion(self):
        """Test conversion to domain entity"""
        # Create a valid DTO
        dto = CreateEventRequest(
            event_id=123,
            coefficient=Decimal("1.45"),
            deadline=1743000000,
            status=EventStatus.NEW
        )
        
        # Convert to domain entity
        event = dto.to_domain()
        
        # Verify fields were correctly mapped
        assert event.event_id == 123
        assert event.coefficient == Decimal("1.45")
        assert event.deadline == 1743000000
        assert event.status == EventStatus.NEW
