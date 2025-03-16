import pytest

from src.domain.vo import EventStatus


class TestEventStatus:
    def test_enum_values(self):
        assert EventStatus.NEW == "NEW"
        assert EventStatus.FINISHED_WIN == "FINISHED_WIN"
        assert EventStatus.FINISHED_LOSE == "FINISHED_LOSE"
    
    def test_string_representation(self):
        assert str(EventStatus.NEW) == "NEW"
        assert str(EventStatus.FINISHED_WIN) == "FINISHED_WIN"
        assert str(EventStatus.FINISHED_LOSE) == "FINISHED_LOSE"
    
    def test_enum_comparison(self):
        assert EventStatus.NEW is EventStatus("NEW")
        assert EventStatus.FINISHED_WIN is EventStatus("FINISHED_WIN")
        assert EventStatus.FINISHED_LOSE is EventStatus("FINISHED_LOSE")
    
    def test_value_uniqueness(self):
        values = [status.value for status in EventStatus]
        assert len(values) == len(set(values))
        assert len(values) == 3
    
    def test_invalid_value(self):
        with pytest.raises(ValueError):
            EventStatus("INVALID_STATUS")
    
    def test_immutability(self):
        with pytest.raises(AttributeError):
            EventStatus.NEW = "MODIFIED"
    
    def test_from_string_valid(self):
        assert EventStatus.from_string("NEW") is EventStatus.NEW
        assert EventStatus.from_string("FINISHED_WIN") is EventStatus.FINISHED_WIN
        assert EventStatus.from_string("FINISHED_LOSE") is EventStatus.FINISHED_LOSE
    
    def test_from_string_invalid(self):
        with pytest.raises(ValueError, match="Недопустимый статус события"):
            EventStatus.from_string("INVALID_STATUS")
    
    def test_is_active_property(self):
        assert EventStatus.NEW.is_active is True
        assert EventStatus.FINISHED_WIN.is_active is False
        assert EventStatus.FINISHED_LOSE.is_active is False
    
    def test_is_finished_property(self):
        assert EventStatus.NEW.is_finished is False
        assert EventStatus.FINISHED_WIN.is_finished is True
        assert EventStatus.FINISHED_LOSE.is_finished is True
