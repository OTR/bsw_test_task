import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.domain.entity.bet import Bet
from src.domain.vo.bet_status import BetStatus


class TestBet:
    """Test suite for the Bet domain entity"""
    
    def test_bet_creation(self):
        """
        Given: Valid bet attributes
        When: Creating a Bet entity
        Then: Bet entity is created with the provided attributes
        """
        # Arrange
        bet_id = 1
        event_id = 123
        amount = Decimal("10.50")
        status = BetStatus.PENDING
        created_at = datetime.now()
        
        # Act
        bet = Bet(
            bet_id=bet_id,
            event_id=event_id,
            amount=amount,
            status=status,
            created_at=created_at
        )
        
        # Assert
        assert bet.bet_id == bet_id
        assert bet.event_id == event_id
        assert bet.amount == amount
        assert bet.status == status
        assert bet.created_at == created_at
    
    def test_bet_creation_with_string_status(self):
        """
        Given: Valid bet attributes with status as string
        When: Creating a Bet entity
        Then: Bet entity is created with the status converted to BetStatus enum
        """
        # Act
        bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50"),
            status="PENDING"
        )
        
        # Assert
        assert bet.status == BetStatus.PENDING
        assert isinstance(bet.status, BetStatus)
    
    def test_bet_creation_with_defaults(self):
        """
        Given: Minimal required bet attributes
        When: Creating a Bet entity
        Then: Bet entity is created with default values for optional attributes
        """
        # Act
        bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50")
        )
        
        # Assert
        assert bet.status == BetStatus.PENDING
        assert isinstance(bet.created_at, datetime)
    
    def test_invalid_amount_negative(self):
        """
        Given: Negative bet amount
        When: Creating a Bet entity
        Then: ValueError is raised
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Bet amount must be a positive number"):
            Bet(
                bet_id=1,
                event_id=123,
                amount=Decimal("-10.50")
            )
    
    def test_invalid_amount_zero(self):
        """
        Given: Zero bet amount
        When: Creating a Bet entity
        Then: ValueError is raised
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Bet amount must be a positive number"):
            Bet(
                bet_id=1,
                event_id=123,
                amount=Decimal("0.00")
            )
    
    def test_invalid_amount_decimal_places(self):
        """
        Given: Bet amount with incorrect decimal places
        When: Creating a Bet entity
        Then: ValueError is raised
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Bet amount must have exactly 2 decimal places"):
            Bet(
                bet_id=1,
                event_id=123,
                amount=Decimal("10.5")
            )
        
        with pytest.raises(ValueError, match="Bet amount must have exactly 2 decimal places"):
            Bet(
                bet_id=1,
                event_id=123,
                amount=Decimal("10.555")
            )
    
    def test_invalid_status(self):
        """
        Given: Invalid bet status
        When: Creating a Bet entity
        Then: ValueError is raised
        """
        # Act & Assert
        with pytest.raises(ValueError):
            Bet(
                bet_id=1,
                event_id=123,
                amount=Decimal("10.50"),
                status="INVALID_STATUS"
            )
    
    def test_is_settled_property(self):
        """
        Given: Bets with different statuses
        When: Checking is_settled property
        Then: Property returns True for settled bets, False for pending bets
        """
        # Arrange
        pending_bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50"),
            status=BetStatus.PENDING
        )
        
        won_bet = Bet(
            bet_id=2,
            event_id=123,
            amount=Decimal("10.50"),
            status=BetStatus.WON
        )
        
        lost_bet = Bet(
            bet_id=3,
            event_id=123,
            amount=Decimal("10.50"),
            status=BetStatus.LOST
        )
        
        # Assert
        assert not pending_bet.is_settled
        assert won_bet.is_settled
        assert lost_bet.is_settled
    
    def test_is_winning_property(self):
        """
        Given: Bets with different statuses
        When: Checking is_winning property
        Then: Property returns True only for won bets
        """
        # Arrange
        pending_bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50"),
            status=BetStatus.PENDING
        )
        
        won_bet = Bet(
            bet_id=2,
            event_id=123,
            amount=Decimal("10.50"),
            status=BetStatus.WON
        )
        
        lost_bet = Bet(
            bet_id=3,
            event_id=123,
            amount=Decimal("10.50"),
            status=BetStatus.LOST
        )
        
        # Assert
        assert not pending_bet.is_winning
        assert won_bet.is_winning
        assert not lost_bet.is_winning
    
    def test_formatted_amount(self):
        """
        Given: A bet with a specific amount
        When: Getting the formatted_amount property
        Then: Amount is properly formatted with currency symbol
        """
        # Arrange
        bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50")
        )
        
        # Assert
        assert bet.formatted_amount == "$10.50"
    
    def test_update_status_from_event_state(self):
        """
        Given: A bet and various event states
        When: Updating the bet status based on event state
        Then: New bet instances are created with the correct status
        """
        # Arrange
        original_bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50")
        )
        
        # Act
        updated_bet_win = original_bet.update_status_from_event_state("FINISHED_WIN")
        updated_bet_lose = original_bet.update_status_from_event_state("FINISHED_LOSE")
        updated_bet_new = original_bet.update_status_from_event_state("NEW")
        
        # Assert
        assert original_bet.status == BetStatus.PENDING
        assert updated_bet_win.status == BetStatus.WON
        assert updated_bet_lose.status == BetStatus.LOST
        assert updated_bet_new.status == BetStatus.PENDING
        
        # Check that the original bet wasn't changed (immutability)
        assert original_bet.status == BetStatus.PENDING
        
        # Check that other properties were preserved
        assert updated_bet_win.bet_id == original_bet.bet_id
        assert updated_bet_win.event_id == original_bet.event_id
        assert updated_bet_win.amount == original_bet.amount
        assert updated_bet_win.created_at == original_bet.created_at
    
    def test_immutability(self):
        """
        Given: A valid bet entity
        When: Attempting to modify its attributes
        Then: FrozenInstanceError is raised
        """
        # Arrange
        bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50")
        )
        
        # Act & Assert
        with pytest.raises(Exception):
            bet.status = BetStatus.WON
        
        with pytest.raises(Exception):
            bet.amount = Decimal("20.00")
    
    def test_json_serialization(self):
        """
        Given: A bet entity
        When: Serializing to JSON
        Then: JSON representation correctly handles Decimal and enum types
        """
        # Arrange
        created_at = datetime(2023, 1, 1, 12, 0, 0)
        bet = Bet(
            bet_id=1,
            event_id=123,
            amount=Decimal("10.50"),
            status=BetStatus.PENDING,
            created_at=created_at
        )
        
        # Act
        json_str = bet.model_dump_json()
        
        # Assert - check that json_str contains the expected values in string format
        assert '"bet_id": 1' in json_str
        assert '"event_id": 123' in json_str
        assert '"amount": "10.50"' in json_str
        assert '"status": "PENDING"' in json_str
        assert "2023-01-01" in json_str
