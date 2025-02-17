import pytest

from src.domain.vo.event_status import EventStatus


class TestEventStatus:
    """Test suite for EventStatus value object"""
    
    def test_enum_values(self):
        """Test that enum has correct values"""
        assert EventStatus.NEW == "NEW"
        assert EventStatus.FINISHED_WIN == "FINISHED_WIN"
        assert EventStatus.FINISHED_LOSE == "FINISHED_LOSE"
    
    def test_string_representation(self):
        """Test string representation of enum values"""
        assert str(EventStatus.NEW) == "NEW"
        assert str(EventStatus.FINISHED_WIN) == "FINISHED_WIN"
        assert str(EventStatus.FINISHED_LOSE) == "FINISHED_LOSE"
    
    def test_enum_comparison(self):
        """Test enum member comparison"""
        assert EventStatus.NEW is EventStatus("NEW")
        assert EventStatus.FINISHED_WIN is EventStatus("FINISHED_WIN")
        assert EventStatus.FINISHED_LOSE is EventStatus("FINISHED_LOSE")
    
    def test_value_uniqueness(self):
        """Test that all enum values are unique"""
        values = [status.value for status in EventStatus]
        assert len(values) == len(set(values))
        assert len(values) == 3
    
    def test_invalid_value(self):
        """Test that invalid values raise ValueError"""
        with pytest.raises(ValueError):
            EventStatus("INVALID_STATUS")
    
    def test_immutability(self):
        """Test that enum values cannot be modified"""
        with pytest.raises(AttributeError):
            EventStatus.NEW = "MODIFIED"
    
    def test_from_string_valid(self):
        """Test from_string method with valid inputs"""
        assert EventStatus.from_string("NEW") is EventStatus.NEW
        assert EventStatus.from_string("FINISHED_WIN") is EventStatus.FINISHED_WIN
        assert EventStatus.from_string("FINISHED_LOSE") is EventStatus.FINISHED_LOSE
    
    def test_from_string_invalid(self):
        """Test from_string method with invalid input"""
        with pytest.raises(ValueError, match="Invalid event status"):
            EventStatus.from_string("INVALID_STATUS")
    
    def test_is_active_property(self):
        """Test is_active property"""
        assert EventStatus.NEW.is_active is True
        assert EventStatus.FINISHED_WIN.is_active is False
        assert EventStatus.FINISHED_LOSE.is_active is False
    
    def test_is_finished_property(self):
        """Test is_finished property"""
        assert EventStatus.NEW.is_finished is False
        assert EventStatus.FINISHED_WIN.is_finished is True
        assert EventStatus.FINISHED_LOSE.is_finished is True
