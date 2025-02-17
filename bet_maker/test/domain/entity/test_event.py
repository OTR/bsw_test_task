import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch
from pydantic_core import ValidationError

from src.domain.entity.event import Event
from src.domain.vo.event_status import EventStatus


class TestEvent:
    """Test suite for Event entity"""
    
    def test_event_creation(self):
        """Test that an event can be created with valid parameters"""
        # Given valid event parameters
        event_id = 123
        coefficient = Decimal("2.50")
        deadline = int(datetime.now().timestamp()) + 3600  # 1 hour from now
        status = EventStatus.NEW
        
        # When creating an Event
        event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=deadline,
            status=status
        )
        
        # Then the event should have the correct attributes
        assert event.event_id == event_id
        assert event.coefficient == coefficient
        assert event.deadline == deadline
        assert event.status == status
    
    def test_event_creation_with_string_status(self):
        """Test that an event can be created with a string status"""
        # Given valid event parameters with string status
        event_id = 123
        coefficient = Decimal("2.50")
        deadline = int(datetime.now().timestamp()) + 3600  # 1 hour from now
        status_str = "NEW"
        
        # When creating an Event
        event = Event(
            event_id=event_id,
            coefficient=coefficient,
            deadline=deadline,
            status=status_str
        )
        
        # Then the event should have the correct attributes with converted status
        assert event.event_id == event_id
        assert event.coefficient == coefficient
        assert event.deadline == deadline
        assert event.status == EventStatus.NEW
        assert isinstance(event.status, EventStatus)
    
    def test_invalid_coefficient_negative(self):
        """Test that creating an event with a negative coefficient raises an error"""
        # Given invalid event parameters with negative coefficient
        event_id = 123
        coefficient = Decimal("-2.50")
        deadline = int(datetime.now().timestamp()) + 3600
        status = EventStatus.NEW
        
        # When attempting to create an Event with negative coefficient
        # Then a ValueError should be raised
        with pytest.raises(ValueError, match="Coefficient must be a positive number"):
            Event(
                event_id=event_id,
                coefficient=coefficient,
                deadline=deadline,
                status=status
            )
    
    def test_invalid_coefficient_decimal_places(self):
        """Test that creating an event with a coefficient with wrong decimal places raises an error"""
        # Given invalid event parameters with coefficient having wrong decimal places
        event_id = 123
        coefficient = Decimal("2.5")  # Only one decimal place
        deadline = int(datetime.now().timestamp()) + 3600
        status = EventStatus.NEW
        
        # When attempting to create an Event with wrong decimal places
        # Then a ValueError should be raised
        with pytest.raises(ValueError, match="Coefficient must have exactly 2 decimal places"):
            Event(
                event_id=event_id,
                coefficient=coefficient,
                deadline=deadline,
                status=status
            )
    
    def test_invalid_status(self):
        """Test that creating an event with an invalid status raises an error"""
        # Given invalid event parameters with invalid status
        event_id = 123
        coefficient = Decimal("2.50")
        deadline = int(datetime.now().timestamp()) + 3600
        status = "INVALID_STATUS"
        
        # When attempting to create an Event with invalid status
        # Then a validation error should be raised
        with pytest.raises(ValidationError):
            Event(
                event_id=event_id,
                coefficient=coefficient,
                deadline=deadline,
                status=status
            )
    
    @patch('src.domain.entity.event.datetime')
    def test_is_active_property_active(self, mock_datetime):
        """Test that is_active property returns True for active events"""
        # Given a fixed current time
        now = datetime.now()
        mock_datetime.now.return_value = now
        
        # And an event with future deadline and NEW status
        future_deadline = int((now + timedelta(hours=1)).timestamp())
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=future_deadline,
            status=EventStatus.NEW
        )
        
        # When checking if the event is active
        # Then it should return True
        assert event.is_active is True
    
    @patch('src.domain.entity.event.datetime')
    def test_is_active_property_inactive_deadline_passed(self, mock_datetime):
        """Test that is_active property returns False for events with passed deadline"""
        # Given a fixed current time
        now = datetime.now()
        mock_datetime.now.return_value = now
        
        # And an event with past deadline and NEW status
        past_deadline = int((now - timedelta(hours=1)).timestamp())
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=past_deadline,
            status=EventStatus.NEW
        )
        
        # When checking if the event is active
        # Then it should return False
        assert event.is_active is False
    
    @patch('src.domain.entity.event.datetime')
    def test_is_active_property_inactive_finished_status(self, mock_datetime):
        """Test that is_active property returns False for events with finished status"""
        # Given a fixed current time
        now = datetime.now()
        mock_datetime.now.return_value = now
        
        # And an event with future deadline but FINISHED_WIN status
        future_deadline = int((now + timedelta(hours=1)).timestamp())
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=future_deadline,
            status=EventStatus.FINISHED_WIN
        )
        
        # When checking if the event is active
        # Then it should return False
        assert event.is_active is False
    
    def test_formatted_deadline(self):
        """Test that formatted_deadline property returns correct string representation"""
        # Given a specific timestamp
        timestamp = 1609459200  # 2021-01-01 00:00:00 UTC
        
        # And an event with that deadline
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=timestamp,
            status=EventStatus.NEW
        )
        
        # When getting the formatted deadline
        formatted = event.formatted_deadline
        
        # Then it should be in the correct format
        expected = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        assert formatted == expected
    
    def test_immutability(self):
        """Test that the Event entity is immutable"""
        # Given an event
        event = Event(
            event_id=123,
            coefficient=Decimal("2.50"),
            deadline=int(datetime.now().timestamp()) + 3600,
            status=EventStatus.NEW
        )
        
        # When attempting to modify attributes
        # Then it should raise a ValidationError
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.event_id = 456
        
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.coefficient = Decimal("3.00")
        
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.deadline = int(datetime.now().timestamp()) + 7200
        
        with pytest.raises(ValidationError, match="frozen_instance"):
            event.status = EventStatus.FINISHED_WIN
