from datetime import datetime, timedelta
from decimal import Decimal

from src.exception.exceptions import InvalidEventDeadlineError
import pytest
from pydantic import ValidationError

from src.domain.entity.event import Event
from src.domain.vo.event_status import EventStatus


class TestEvent:
    """Test suite for Event model"""

    @pytest.fixture
    def future_timestamp(self) -> int:
        """Fixture providing a timestamp 1 hour in the future"""
        return int((datetime.now() + timedelta(hours=1)).timestamp())

    @pytest.fixture
    def valid_event_data(self, future_timestamp: int) -> dict:
        """Fixture providing valid event data"""
        return {
            "event_id": 1,
            "coefficient": Decimal("1.50"),
            "deadline": future_timestamp,
            "status": EventStatus.NEW
        }

    def test_create_valid_event(self, valid_event_data: dict):
        """Test creating a valid event"""
        event = Event(**valid_event_data)
        assert event.event_id == valid_event_data["event_id"]
        assert event.coefficient == valid_event_data["coefficient"]
        assert event.deadline == valid_event_data["deadline"]
        assert event.status == valid_event_data["status"]

    def test_event_id_validation(self, valid_event_data: dict):
        """Test event_id validation"""
        # Test negative event_id
        with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
            valid_event_data["event_id"] = -1
            Event(**valid_event_data)

        # Test non-integer event_id
        with pytest.raises(ValidationError, match="Input should be a valid integer"):
            valid_event_data["event_id"] = "abc"
            Event(**valid_event_data)

    def test_coefficient_validation(self, valid_event_data: dict):
        """Test coefficient validation"""
        # Test negative coefficient
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            valid_event_data["coefficient"] = Decimal("-1.50")
            Event(**valid_event_data)

        # Test zero coefficient
        with pytest.raises(ValidationError, match="Input should be greater than 0"):
            valid_event_data["coefficient"] = Decimal("0.00")
            Event(**valid_event_data)

        # Test more than 2 decimal places
        with pytest.raises(ValidationError, match="Decimal input should have no more than 2 decimal places"):
            valid_event_data["coefficient"] = Decimal("1.505")
            Event(**valid_event_data)

    def test_deadline_validation(self, valid_event_data: dict):
        """Test deadline validation"""
        # Test past deadline
        past_timestamp = int((datetime.now() - timedelta(hours=1)).timestamp())
        with pytest.raises(InvalidEventDeadlineError, match="must be in the future"):
            valid_event_data["deadline"] = past_timestamp
            Event(**valid_event_data)

        # Test current timestamp
        current_timestamp = int(datetime.now().timestamp())
        with pytest.raises(InvalidEventDeadlineError, match="must be in the future"):
            valid_event_data["deadline"] = current_timestamp
            Event(**valid_event_data)

    def test_status_validation(self, valid_event_data: dict):
        """Test status validation"""
        # Test invalid status
        with pytest.raises(ValidationError, match="Input should be 'NEW', 'FINISHED_WIN' or 'FINISHED_LOSE'"):
            valid_event_data["status"] = "INVALID_STATUS"
            Event(**valid_event_data)

        # Test all valid statuses
        for status in EventStatus:
            valid_event_data["status"] = status
            event = Event(**valid_event_data)
            assert event.status == status

    def test_is_finished_property(self, valid_event_data: dict):
        """Test is_finished property"""
        # Test NEW status
        event = Event(**valid_event_data)
        assert not event.is_finished

        # Test FINISHED_WIN status
        event.status = EventStatus.FINISHED_WIN
        assert event.is_finished

        # Test FINISHED_LOSE status
        event.status = EventStatus.FINISHED_LOSE
        assert event.is_finished

    def test_is_active_property(self, valid_event_data: dict):
        """Test is_active property"""
        # Test active event (NEW status and future deadline)
        event = Event(**valid_event_data)
        assert event.is_active

        # Test inactive due to finished status
        event.status = EventStatus.FINISHED_WIN
        assert not event.is_active

        # Test inactive due to passed deadline
        event.status = EventStatus.NEW
        event.deadline = int((datetime.now() - timedelta(hours=1)).timestamp())
        assert not event.is_active
