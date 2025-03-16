import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch
from pydantic_core import ValidationError

from src.domain.entity import Event
from src.domain.vo import EventStatus


class TestEvent:
    def test_event_creation(self):
        event_id = 123
        coefficient = Decimal("2.50")
        deadline = int(datetime.now().timestamp()) + 3600
        status = EventStatus.NEW
        event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=deadline,
            status=status
        )
        assert event.event_id == event_id
        assert event.coefficient == coefficient
        assert event.deadline == deadline
        assert event.status == status

    def test_event_creation_with_string_status(self):
        event_id = 123
        coefficient = Decimal("2.50")
        deadline = int(datetime.now().timestamp()) + 3600
        status_str = "NEW"
        event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=deadline,
            status=status_str
        )
        assert event.event_id == event_id
        assert event.coefficient == coefficient
        assert event.deadline == deadline
        assert event.status == EventStatus.NEW
        assert isinstance(event.status, EventStatus)

    def test_invalid_coefficient_negative(self):
        event_id = 123
        coefficient = Decimal("-2.50")
        deadline = int(datetime.now().timestamp()) + 3600
        status = EventStatus.NEW
        with pytest.raises(ValueError, match="Coefficient must be a positive number"):
            Event(
                event_id=event_id,
                coefficient=coefficient,
                deadline=deadline,
                status=status
            )

    def test_invalid_coefficient_decimal_places(self):
        event_id = 123
        coefficient = Decimal("2.5")
        deadline = int(datetime.now().timestamp()) + 3600
        status = EventStatus.NEW
        with pytest.raises(ValueError, match="Coefficient must have exactly 2 decimal places"):
            Event(
                event_id=event_id,
                coefficient=coefficient,
                deadline=deadline,
                status=status
            )

    def test_invalid_status(self):
        event_id = 123
        coefficient = Decimal("2.50")
        deadline = int(datetime.now().timestamp()) + 3600
        status = "INVALID_STATUS"
        with pytest.raises(ValidationError):
            Event(
                event_id=event_id,
                coefficient=coefficient,
                deadline=deadline,
                status=status
            )

    @patch('src.domain.entity.event.datetime')
    def test_is_active_property_active(self, mock_datetime):
        now = datetime.now()
        mock_datetime.now.return_value = now
        future_deadline = int((now + timedelta(hours=1)).timestamp())
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=future_deadline,
            status=EventStatus.NEW
        )
        assert event.is_active is True

    @patch('src.domain.entity.event.datetime')
    def test_is_active_property_inactive_deadline_passed(self, mock_datetime):
        now = datetime.now()
        mock_datetime.now.return_value = now
        past_deadline = int((now - timedelta(hours=1)).timestamp())
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=past_deadline,
            status=EventStatus.NEW
        )
        assert event.is_active is False

    @patch('src.domain.entity.event.datetime')
    def test_is_active_property_inactive_finished_status(self, mock_datetime):
        now = datetime.now()
        mock_datetime.now.return_value = now
        future_deadline = int((now + timedelta(hours=1)).timestamp())
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=future_deadline,
            status=EventStatus.FINISHED_WIN
        )
        assert event.is_active is False

    def test_formatted_deadline(self):
        timestamp = 1609459200
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=timestamp,
            status=EventStatus.NEW
        )
        formatted = event.formatted_deadline
        expected = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        assert formatted == expected

    def test_immutability(self):
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=int(datetime.now().timestamp()) + 3600,
            status=EventStatus.NEW
        )
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.event_id = 456
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.coefficient = Decimal("3.00")
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.deadline = int(datetime.now().timestamp()) + 7200
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.status = EventStatus.FINISHED_WIN
