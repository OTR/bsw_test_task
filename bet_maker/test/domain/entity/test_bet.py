import pytest
from decimal import Decimal
from datetime import datetime

from src.domain.entity import Bet
from src.domain.vo import BetStatus


class TestBet:
    def test_bet_creation(self):
        bet_id = 1
        event_id = 123
        amount = Decimal("10.50")
        status = BetStatus.PENDING
        created_at = datetime.now()
        bet = Bet(bet_id=bet_id, event_id=event_id, amount=amount, status=status, created_at=created_at)
        assert bet.bet_id == bet_id
        assert bet.event_id == event_id
        assert bet.amount == amount
        assert bet.status == status
        assert bet.created_at == created_at

    def test_bet_creation_with_string_status(self):
        bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"), status="PENDING")
        assert bet.status == BetStatus.PENDING
        assert isinstance(bet.status, BetStatus)

    def test_bet_creation_with_defaults(self):
        bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"))
        assert bet.status == BetStatus.PENDING
        assert isinstance(bet.created_at, datetime)

    def test_invalid_amount_negative(self):
        with pytest.raises(ValueError, match="Сумма ставки должна быть положительной"):
            Bet(bet_id=1, event_id=123, amount=Decimal("-10.50"))

    def test_invalid_amount_zero(self):
        with pytest.raises(ValueError, match="Сумма ставки должна быть положительной"):
            Bet(bet_id=1, event_id=123, amount=Decimal("0.00"))

    def test_invalid_amount_decimal_places(self):
        with pytest.raises(ValueError, match="Сумма ставки должна иметь ровно 2 знака после запятой"):
            Bet(bet_id=1, event_id=123, amount=Decimal("10.5"))
        with pytest.raises(ValueError, match="Сумма ставки должна иметь ровно 2 знака после запятой"):
            Bet(bet_id=1, event_id=123, amount=Decimal("10.555"))

    def test_invalid_status(self):
        with pytest.raises(ValueError):
            Bet(bet_id=1, event_id=123, amount=Decimal("10.50"), status="INVALID_STATUS")

    def test_is_settled_property(self):
        pending_bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"), status=BetStatus.PENDING)
        won_bet = Bet(bet_id=2, event_id=123, amount=Decimal("10.50"), status=BetStatus.WON)
        lost_bet = Bet(bet_id=3, event_id=123, amount=Decimal("10.50"), status=BetStatus.LOST)
        assert not pending_bet.is_settled
        assert won_bet.is_settled
        assert lost_bet.is_settled

    def test_is_winning_property(self):
        pending_bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"), status=BetStatus.PENDING)
        won_bet = Bet(bet_id=2, event_id=123, amount=Decimal("10.50"), status=BetStatus.WON)
        lost_bet = Bet(bet_id=3, event_id=123, amount=Decimal("10.50"), status=BetStatus.LOST)
        assert not pending_bet.is_winning
        assert won_bet.is_winning
        assert not lost_bet.is_winning

    def test_formatted_amount(self):
        bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"))
        assert bet.formatted_amount == "$10.50"

    def test_update_status_from_event_state(self):
        original_bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"))
        updated_bet_win = original_bet.update_status_from_event_state("FINISHED_WIN")
        updated_bet_lose = original_bet.update_status_from_event_state("FINISHED_LOSE")
        updated_bet_new = original_bet.update_status_from_event_state("NEW")
        assert original_bet.status == BetStatus.PENDING
        assert updated_bet_win.status == BetStatus.WON
        assert updated_bet_lose.status == BetStatus.LOST
        assert updated_bet_new.status == BetStatus.PENDING
        assert original_bet.status == BetStatus.PENDING
        assert updated_bet_win.bet_id == original_bet.bet_id
        assert updated_bet_win.event_id == original_bet.event_id
        assert updated_bet_win.amount == original_bet.amount
        assert updated_bet_win.created_at == original_bet.created_at

    def test_immutability(self):
        bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"))
        with pytest.raises(Exception):
            bet.status = BetStatus.WON
        with pytest.raises(Exception):
            bet.amount = Decimal("20.00")

    def test_json_serialization(self):
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        bet = Bet(bet_id=1, event_id=123, amount=Decimal("10.50"), status=BetStatus.PENDING, created_at=created_at)
        json_str = bet.model_dump_json()
        assert '"bet_id": 1' in json_str
        assert '"event_id": 123' in json_str
        assert '"amount": "10.50"' in json_str
        assert '"status": "PENDING"' in json_str
        assert "2023-01-01" in json_str
