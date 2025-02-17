import pytest

from src.domain.vo.bet_status import BetStatus


class TestBetStatus:
    """Test suite for BetStatus value object"""

    def test_enum_values(self):
        """Test that enum has correct values"""
        assert BetStatus.PENDING == "PENDING"
        assert BetStatus.WON == "WON"
        assert BetStatus.LOST == "LOST"

    def test_string_representation(self):
        """Test string representation of enum values"""
        assert str(BetStatus.PENDING) == "PENDING"
        assert str(BetStatus.WON) == "WON"
        assert str(BetStatus.LOST) == "LOST"

    def test_enum_comparison(self):
        """Test enum member comparison"""
        assert BetStatus.PENDING is BetStatus("PENDING")
        assert BetStatus.WON is BetStatus("WON")
        assert BetStatus.LOST is BetStatus("LOST")

    def test_value_uniqueness(self):
        """Test that all enum values are unique"""
        values = [status.value for status in BetStatus]
        assert len(values) == len(set(values))
        assert len(values) == 3

    def test_invalid_value(self):
        """Test that invalid values raise ValueError"""
        with pytest.raises(ValueError):
            BetStatus("INVALID_STATUS")

    def test_immutability(self):
        """Test that enum values cannot be modified"""
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
        """Test mapping from event state to bet status"""
        assert BetStatus.from_event_state(event_state) is expected_status

    def test_classmethod_binding(self):
        """Test that from_event_state is properly bound as a class method"""
        # This test replaces the problematic subclass test
        
        # Verify the method is bound to the class
        assert hasattr(BetStatus, 'from_event_state')
        
        # Ensure it's a classmethod by checking the descriptor
        import inspect
        assert isinstance(inspect.getattr_static(BetStatus, 'from_event_state'), classmethod)
        
        # Test that it returns the expected instance
        result = BetStatus.from_event_state("FINISHED_WIN")
        assert result is BetStatus.WON
        assert isinstance(result, BetStatus)

    def test_member_iteration(self):
        """Test that all members can be iterated"""
        statuses = list(BetStatus)
        assert len(statuses) == 3
        assert BetStatus.PENDING in statuses
        assert BetStatus.WON in statuses
        assert BetStatus.LOST in statuses

    def test_str_dunder_method(self):
        """Test __str__ method explicitly"""
        assert BetStatus.PENDING.__str__() == "PENDING"
        assert BetStatus.WON.__str__() == "WON"
        assert BetStatus.LOST.__str__() == "LOST"