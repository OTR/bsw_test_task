import pytest
from src.domain.vo.event_status import EventStatus


class TestEventStatus:
    """Test suite for EventStatus enum"""

    def test_enum_values(self):
        """Test that enum has correct values"""
        assert EventStatus.NEW == "NEW"
        assert EventStatus.FINISHED_WIN == "FINISHED_WIN"
        assert EventStatus.FINISHED_LOSE == "FINISHED_LOSE"

    def test_string_representation(self):
        """Test string representation of enum values"""
        assert str(EventStatus.NEW) == "EventStatus.NEW"
        assert str(EventStatus.FINISHED_WIN) == "EventStatus.FINISHED_WIN"
        assert str(EventStatus.FINISHED_LOSE) == "EventStatus.FINISHED_LOSE"

    def test_enum_comparison(self):
        """Test enum member comparison"""
        assert EventStatus.NEW is EventStatus("NEW")
        assert EventStatus.FINISHED_WIN is EventStatus("FINISHED_WIN")
        assert EventStatus.FINISHED_LOSE is EventStatus("FINISHED_LOSE")

    def test_value_uniqueness(self):
        """Test that all enum values are unique"""
        values = [status.value for status in EventStatus]
        assert len(values) == len(set(values))

    def test_invalid_value(self):
        """Test that invalid values raise ValueError"""
        with pytest.raises(ValueError):
            EventStatus("INVALID_STATUS")

    def test_immutability(self):
        """Test that enum values cannot be modified"""
        with pytest.raises(AttributeError):
            EventStatus.NEW = "MODIFIED"