import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union
from unittest.mock import AsyncMock, patch, MagicMock

from src.domain.entity.bet import Bet
from src.domain.vo.bet_status import BetStatus
from src.domain.repository.base_bet_repository import BaseBetRepository
from src.exception import BetNotFoundError, BetCreationError

pytestmark = pytest.mark.asyncio


class MockBetRepository(BaseBetRepository):
    """Mock implementation of BaseBetRepository for testing purposes"""
    
    def __init__(self, bets: List[Dict[str, Any]] = None):
        self.bets = {}
        self.next_id = 1
        if bets:
            for bet_data in bets:
                bet = Bet.model_validate(bet_data)
                self.bets[bet.bet_id] = bet
                if isinstance(bet.bet_id, int) and bet.bet_id >= self.next_id:
                    self.next_id = bet.bet_id + 1
        
        # Create mocks for tracking calls
        self.get_all_mock = AsyncMock(side_effect=self._get_all)
        self.get_by_id_mock = AsyncMock(side_effect=self._get_by_id)
        self.create_mock = AsyncMock(side_effect=self._create)
        self.get_by_event_id_mock = AsyncMock(side_effect=self._get_by_event_id)
        self.get_by_status_mock = AsyncMock(side_effect=self._get_by_status)
        self.update_status_mock = AsyncMock(side_effect=self._update_status)
        self.filter_bets_mock = AsyncMock(side_effect=self._filter_bets)
        self.exists_mock = AsyncMock(side_effect=self._exists)
    
    async def get_all(self) -> List[Bet]:
        return await self.get_all_mock()
    
    async def _get_all(self) -> List[Bet]:
        return list(self.bets.values())
    
    async def get_by_id(self, bet_id: Union[int, str]) -> Bet:
        return await self.get_by_id_mock(bet_id)
    
    async def _get_by_id(self, bet_id: Union[int, str]) -> Bet:
        if bet_id not in self.bets:
            raise BetNotFoundError(bet_id)
        return self.bets[bet_id]
    
    async def create(self, bet: Bet) -> Bet:
        return await self.create_mock(bet)
    
    async def _create(self, bet: Bet) -> Bet:
        # Generate a new ID
        new_bet_id = self.next_id
        self.next_id += 1
        
        # Create a new bet with the ID
        new_bet = Bet.model_validate({
            "bet_id": new_bet_id,
            "event_id": bet.event_id,
            "amount": bet.amount,
            "status": bet.status,
            "created_at": bet.created_at
        })
        
        # Store the bet
        self.bets[new_bet_id] = new_bet
        return new_bet
    
    async def get_by_event_id(self, event_id: Union[int, str]) -> List[Bet]:
        return await self.get_by_event_id_mock(event_id)
    
    async def _get_by_event_id(self, event_id: Union[int, str]) -> List[Bet]:
        return [bet for bet in self.bets.values() if bet.event_id == event_id]
    
    async def get_by_status(self, status: BetStatus) -> List[Bet]:
        return await self.get_by_status_mock(status)
    
    async def _get_by_status(self, status: BetStatus) -> List[Bet]:
        return [bet for bet in self.bets.values() if bet.status == status]
    
    async def update_status(self, bet_id: Union[int, str], new_status: BetStatus) -> Bet:
        return await self.update_status_mock(bet_id, new_status)
    
    async def _update_status(self, bet_id: Union[int, str], new_status: BetStatus) -> Bet:
        if bet_id not in self.bets:
            raise BetNotFoundError(bet_id)
        
        # Get existing bet
        existing_bet = self.bets[bet_id]
        
        # Create a new bet with updated status (since Bet is immutable)
        updated_bet = Bet.model_validate({
            "bet_id": existing_bet.bet_id,
            "event_id": existing_bet.event_id,
            "amount": existing_bet.amount,
            "status": new_status,
            "created_at": existing_bet.created_at
        })
        
        # Update in storage
        self.bets[bet_id] = updated_bet
        return updated_bet
    
    async def filter_bets(
        self,
        event_id: Optional[Union[int, str]] = None,
        status: Optional[BetStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Bet]:
        return await self.filter_bets_mock(event_id, status, created_after, created_before)
    
    async def _filter_bets(
        self,
        event_id: Optional[Union[int, str]] = None,
        status: Optional[BetStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Bet]:
        result = list(self.bets.values())
        
        if event_id is not None:
            result = [bet for bet in result if bet.event_id == event_id]
        
        if status is not None:
            result = [bet for bet in result if bet.status == status]
        
        if created_after is not None:
            result = [bet for bet in result if bet.created_at > created_after]
        
        if created_before is not None:
            result = [bet for bet in result if bet.created_at < created_before]
        
        return result
    
    async def exists(self, bet_id: Union[int, str]) -> bool:
        return await self.exists_mock(bet_id)
    
    async def _exists(self, bet_id: Union[int, str]) -> bool:
        return bet_id in self.bets


@pytest.fixture
def sample_bets():
    """Fixture providing sample bet data for testing"""
    now = datetime.now()
    earlier = now - timedelta(hours=1)
    much_earlier = now - timedelta(days=1)
    
    return [
        {
            "bet_id": 1,
            "event_id": 101,
            "amount": Decimal("10.00"),
            "status": BetStatus.PENDING,
            "created_at": now
        },
        {
            "bet_id": 2,
            "event_id": 101,
            "amount": Decimal("20.00"),
            "status": BetStatus.WON,
            "created_at": earlier
        },
        {
            "bet_id": 3,
            "event_id": 102,
            "amount": Decimal("30.00"),
            "status": BetStatus.LOST,
            "created_at": earlier
        },
        {
            "bet_id": 4,
            "event_id": 103,
            "amount": Decimal("40.00"),
            "status": BetStatus.PENDING,
            "created_at": much_earlier
        }
    ]


@pytest.fixture
def mock_repository(sample_bets):
    """Fixture providing a mock repository initialized with sample bets"""
    return MockBetRepository(sample_bets)


class TestBaseBetRepository:
    """Test suite for the BaseBetRepository abstract base class"""
    
    async def test_get_all(self, mock_repository, sample_bets):
        """
        Given: A repository with sample bets
        When: Calling get_all method
        Then: All bets should be returned
        """
        # Act
        bets = await mock_repository.get_all()
        
        # Assert
        assert len(bets) == len(sample_bets)
        assert mock_repository.get_all_mock.called
    
    async def test_get_by_id_existing(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Calling get_by_id with an existing bet ID
        Then: The correct bet should be returned
        """
        # Act
        bet = await mock_repository.get_by_id(1)
        
        # Assert
        assert bet.bet_id == 1
        assert bet.amount == Decimal("10.00")
        assert bet.status == BetStatus.PENDING
        assert mock_repository.get_by_id_mock.called
    
    async def test_get_by_id_nonexistent(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Calling get_by_id with a non-existent bet ID
        Then: BetNotFoundError should be raised
        """
        # Act & Assert
        with pytest.raises(BetNotFoundError) as exc_info:
            await mock_repository.get_by_id(999)
        
        assert "999" in str(exc_info.value)
        assert mock_repository.get_by_id_mock.called
    
    async def test_create(self, mock_repository):
        """
        Given: A repository
        When: Creating a new bet
        Then: The bet should be created with a new ID and stored in the repository
        """
        # Arrange - use a placeholder ID that doesn't exist in the repository
        next_expected_id = mock_repository.next_id
        now = datetime.now()
        bet_data = {
            "bet_id": 999,  # Temporary ID for model validation, different from what repository will assign
            "event_id": 105,
            "amount": Decimal("50.00"),
            "status": BetStatus.PENDING,
            "created_at": now
        }
        new_bet = Bet.model_validate(bet_data)
        
        # Get the current count of bets
        initial_count = len(await mock_repository.get_all())
        
        # Act
        created_bet = await mock_repository.create(new_bet)
        
        # Assert
        assert created_bet.bet_id is not None
        assert created_bet.bet_id != 999  # Should have a new ID assigned by repository
        assert created_bet.bet_id == next_expected_id  # Should match the expected next ID
        assert created_bet.event_id == 105
        assert created_bet.amount == Decimal("50.00")
        assert mock_repository.create_mock.called
        
        # Verify the bet was stored
        stored_bet = await mock_repository.get_by_id(created_bet.bet_id)
        assert stored_bet == created_bet
        
        # Verify we have one more bet now
        final_count = len(await mock_repository.get_all())
        assert final_count == initial_count + 1
    
    async def test_get_by_event_id(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Calling get_by_event_id
        Then: Only bets for the specified event should be returned
        """
        # Act
        event_bets = await mock_repository.get_by_event_id(101)
        
        # Assert
        assert len(event_bets) == 2
        assert all(bet.event_id == 101 for bet in event_bets)
        assert mock_repository.get_by_event_id_mock.called
    
    async def test_get_by_status(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Calling get_by_status
        Then: Only bets with the specified status should be returned
        """
        # Act
        pending_bets = await mock_repository.get_by_status(BetStatus.PENDING)
        won_bets = await mock_repository.get_by_status(BetStatus.WON)
        lost_bets = await mock_repository.get_by_status(BetStatus.LOST)
        
        # Assert
        assert len(pending_bets) == 2
        assert all(bet.status == BetStatus.PENDING for bet in pending_bets)
        
        assert len(won_bets) == 1
        assert all(bet.status == BetStatus.WON for bet in won_bets)
        
        assert len(lost_bets) == 1
        assert all(bet.status == BetStatus.LOST for bet in lost_bets)
        
        assert mock_repository.get_by_status_mock.call_count == 3
    
    async def test_update_status(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Updating the status of a bet
        Then: The bet should have the new status
        """
        # Act
        updated_bet = await mock_repository.update_status(1, BetStatus.WON)
        
        # Assert
        assert updated_bet.bet_id == 1
        assert updated_bet.status == BetStatus.WON
        assert mock_repository.update_status_mock.called
        
        # Verify the bet was updated in storage
        stored_bet = await mock_repository.get_by_id(1)
        assert stored_bet.status == BetStatus.WON
    
    async def test_update_status_nonexistent(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Updating the status of a non-existent bet
        Then: BetNotFoundError should be raised
        """
        # Act & Assert
        with pytest.raises(BetNotFoundError) as exc_info:
            await mock_repository.update_status(999, BetStatus.WON)
        
        assert "999" in str(exc_info.value)
        assert mock_repository.update_status_mock.called
    
    async def test_filter_bets_by_event_id(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Filtering bets by event_id
        Then: Only bets for the specified event should be returned
        """
        # Act
        filtered_bets = await mock_repository.filter_bets(event_id=101)
        
        # Assert
        assert len(filtered_bets) == 2
        assert all(bet.event_id == 101 for bet in filtered_bets)
        assert mock_repository.filter_bets_mock.called
        assert mock_repository.filter_bets_mock.call_args[0][0] == 101
    
    async def test_filter_bets_by_status(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Filtering bets by status
        Then: Only bets with the specified status should be returned
        """
        # Act
        filtered_bets = await mock_repository.filter_bets(status=BetStatus.PENDING)
        
        # Assert
        assert len(filtered_bets) == 2
        assert all(bet.status == BetStatus.PENDING for bet in filtered_bets)
        assert mock_repository.filter_bets_mock.called
        assert mock_repository.filter_bets_mock.call_args[0][1] == BetStatus.PENDING
    
    async def test_filter_bets_by_created_timeframe(self, mock_repository, sample_bets):
        """
        Given: A repository with sample bets
        When: Filtering bets by creation timeframe
        Then: Only bets created within the specified timeframe should be returned
        """
        # Get a reference time
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        
        # Act - get bets created in the last hour
        recent_bets = await mock_repository.filter_bets(created_after=one_hour_ago)
        
        # Act - get bets created in the last day but more than an hour ago
        older_bets = await mock_repository.filter_bets(created_after=one_day_ago, created_before=one_hour_ago)
        
        # Assert
        assert len(recent_bets) >= 1  # At least the first sample bet should be included
        assert len(older_bets) >= 1  # At least one of the other sample bets should be included
        
        assert all(bet.created_at > one_hour_ago for bet in recent_bets)
        assert all(one_day_ago < bet.created_at < one_hour_ago for bet in older_bets)
        
        assert mock_repository.filter_bets_mock.call_count == 2
    
    async def test_filter_bets_combined_criteria(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Filtering bets with multiple criteria
        Then: Only bets matching all criteria should be returned
        """
        # Get a reference time
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Act - get PENDING bets for event 101 created in the last hour
        filtered_bets = await mock_repository.filter_bets(
            event_id=101,
            status=BetStatus.PENDING,
            created_after=one_hour_ago
        )
        
        # Assert
        assert all(
            bet.event_id == 101 and
            bet.status == BetStatus.PENDING and
            bet.created_at > one_hour_ago
            for bet in filtered_bets
        )
        
        assert mock_repository.filter_bets_mock.called
    
    async def test_exists(self, mock_repository):
        """
        Given: A repository with sample bets
        When: Checking if bets exist
        Then: The repository should correctly report existence
        """
        # Act & Assert
        assert await mock_repository.exists(1) is True
        assert await mock_repository.exists(999) is False
        
        assert mock_repository.exists_mock.call_count == 2