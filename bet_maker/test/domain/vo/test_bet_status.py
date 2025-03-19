import pytest

from src.domain.vo import BetStatus


class TestBetStatus:
    def test_enum_values(self):
        assert BetStatus.PENDING == "PENDING"
        assert BetStatus.WON == "WON"
        assert BetStatus.LOST == "LOST"

    def test_string_representation(self):
        assert str(BetStatus.PENDING) == "PENDING"
        assert str(BetStatus.WON) == "WON"
        assert str(BetStatus.LOST) == "LOST"

    def test_enum_comparison(self):
        assert BetStatus.PENDING is BetStatus("PENDING")
        assert BetStatus.WON is BetStatus("WON")
        assert BetStatus.LOST is BetStatus("LOST")

    def test_value_uniqueness(self):
        values = [status.value for status in BetStatus]
        assert len(values) == len(set(values))
        assert len(values) == 3

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            BetStatus("INVALID_STATUS")

    def test_immutability(self):
        with pytest.raises(AttributeError):
            BetStatus.PENDING = "MODIFIED"

    @pytest.mark.parametrize(
        "event_state,expected_status",
        [
            ("NEW", BetStatus.PENDING),
            ("UNKNOWN", BetStatus.PENDING),
            ("FINISHED_WIN", BetStatus.WON),
            ("FINISHED_LOSE", BetStatus.LOST),
            (None, BetStatus.PENDING),
            ("", BetStatus.PENDING),
        ],
    )
    def test_from_event_state(self, event_state, expected_status):
        assert BetStatus.from_event_state(event_state) is expected_status

    def test_classmethod_binding(self):
        assert hasattr(BetStatus, 'from_event_state')

        import inspect
        assert isinstance(inspect.getattr_static(BetStatus, 'from_event_state'), classmethod)

        result = BetStatus.from_event_state("FINISHED_WIN")
        assert result is BetStatus.WON
        assert isinstance(result, BetStatus)

    def test_member_iteration(self):
        statuses = list(BetStatus)
        assert len(statuses) == 3
        assert BetStatus.PENDING in statuses
        assert BetStatus.WON in statuses
        assert BetStatus.LOST in statuses

    def test_str_dunder_method(self):
        assert BetStatus.PENDING.__str__() == "PENDING"
        assert BetStatus.WON.__str__() == "WON"
        assert BetStatus.LOST.__str__() == "LOST"
