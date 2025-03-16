import pytest
from src.domain.vo import EventStatus


class TestEventStatus:
    def test_enum_values(self):
        assert EventStatus.NEW == "NEW"
        assert EventStatus.FINISHED_WIN == "FINISHED_WIN"
        assert EventStatus.FINISHED_LOSE == "FINISHED_LOSE"

    def test_string_representation(self):
        assert str(EventStatus.NEW) == "EventStatus.NEW"
        assert str(EventStatus.FINISHED_WIN) == "EventStatus.FINISHED_WIN"
        assert str(EventStatus.FINISHED_LOSE) == "EventStatus.FINISHED_LOSE"

    def test_enum_comparison(self):
        assert EventStatus.NEW is EventStatus("NEW")
        assert EventStatus.FINISHED_WIN is EventStatus("FINISHED_WIN")
        assert EventStatus.FINISHED_LOSE is EventStatus("FINISHED_LOSE")

    def test_value_uniqueness(self):
        values = [status.value for status in EventStatus]
        assert len(values) == len(set(values))

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            EventStatus("INVALID_STATUS")

    def test_immutability(self):
        with pytest.raises(AttributeError):
            EventStatus.NEW = "MODIFIED"
    