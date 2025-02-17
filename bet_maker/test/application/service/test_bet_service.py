import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

from src.application.service.bet_service import BetService
from src.domain.entity.bet import Bet, BetRequest, BetResponse
from src.domain.entity.event import Event
from src.domain.vo.bet_status import BetStatus
from src.domain.vo.event_status import EventStatus
from src.exception import (
    BetCreationError,
    BetNotFoundError, 
    EventNotFoundError, 
)


@pytest.fixture
def mock_bet_repository():
    """Create a mock bet repository with predefined behavior"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_event_repository():
    """Create a mock event repository with predefined behavior"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def bet_service(mock_bet_repository, mock_event_repository):
    """Create a BetService instance with mock repositories"""
    return BetService(
        bet_repository=mock_bet_repository,
        event_repository=mock_event_repository
    )


@pytest.fixture
def sample_events():
    """Create sample events for testing"""
    now = datetime.now()
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    
    return [
        Event(
            event_id=1,
            coefficient=Decimal("1.50"),
            deadline=int(future.timestamp()),
            status=EventStatus.NEW
        ),
        Event(
            event_id=2,
            coefficient=Decimal("2.00"),
            deadline=int(future.timestamp()),
            status=EventStatus.FINISHED_WIN
        ),
        Event(
            event_id=3,
            coefficient=Decimal("3.00"),
            deadline=int(past.timestamp()),
            status=EventStatus.NEW
        ),
        Event(
            event_id=4,
            coefficient=Decimal("4.00"),
            deadline=int(past.timestamp()),
            status=EventStatus.FINISHED_LOSE
        ),
    ]


@pytest.fixture
def sample_bets():
    """Create sample bets for testing"""
    now = datetime.now()
    return [
        Bet(
            bet_id=1,
            event_id=1,
            amount=Decimal("10.00"),
            status=BetStatus.PENDING,
            created_at=now
        ),
        Bet(
            bet_id=2,
            event_id=2,
            amount=Decimal("20.00"),
            status=BetStatus.PENDING,
            created_at=now
        ),
        Bet(
            bet_id=3,
            event_id=3,
            amount=Decimal("30.00"),
            status=BetStatus.PENDING,
            created_at=now
        ),
        Bet(
            bet_id=4,
            event_id=4,
            amount=Decimal("40.00"),
            status=BetStatus.PENDING,
            created_at=now
        ),
    ]


class TestBetService:
    """Test suite for the BetService class"""
    
    @pytest.mark.asyncio
    async def test_get_all_bets(self, bet_service, mock_bet_repository, sample_bets):
        """
        GIVEN a repository with bets
        WHEN get_all_bets() is called
        THEN it should return all bets from the repository
        """
        # Arrange
        mock_bet_repository.get_all.return_value = sample_bets
        
        # Act
        result = await bet_service.get_all_bets()
        
        # Assert
        assert len(result) == len(sample_bets)
        assert all(isinstance(bet, BetResponse) for bet in result)
        mock_bet_repository.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_bet_by_id(self, bet_service, mock_bet_repository, sample_bets):
        """
        GIVEN a repository with bets
        WHEN get_bet_by_id() is called with a valid ID
        THEN it should return the bet with that ID
        """
        # Arrange
        bet = sample_bets[0]
        mock_bet_repository.get_by_id.return_value = bet
        
        # Act
        result = await bet_service.get_bet_by_id(1)
        
        # Assert
        assert isinstance(result, BetResponse)
        assert result.bet_id == bet.bet_id
        mock_bet_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_bet_by_id_not_found(self, bet_service, mock_bet_repository):
        """
        GIVEN a repository where a bet doesn't exist
        WHEN get_bet_by_id() is called with a non-existent ID
        THEN it should raise BetNotFoundError
        """
        # Arrange
        mock_bet_repository.get_by_id.side_effect = BetNotFoundError(bet_id=999)
        
        # Act & Assert
        with pytest.raises(BetNotFoundError) as exc_info:
            await bet_service.get_bet_by_id(999)
        
        assert "999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_bets_by_event(self, bet_service, mock_bet_repository, sample_bets):
        """
        GIVEN a repository with bets for different events
        WHEN get_bets_by_event() is called with an event ID
        THEN it should return only bets for that event
        """
        # Arrange
        event_bets = [b for b in sample_bets if b.event_id == 1]
        mock_bet_repository.get_by_event_id.return_value = event_bets
        
        # Act
        result = await bet_service.get_bets_by_event(1)
        
        # Assert
        assert len(result) == len(event_bets)
        assert all(bet.event_id == 1 for bet in result)
        mock_bet_repository.get_by_event_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_bets_by_status(self, bet_service, mock_bet_repository, sample_bets):
        """
        GIVEN a repository with bets of different statuses
        WHEN get_bets_by_status() is called with a status
        THEN it should return only bets with that status
        """
        # Arrange
        pending_bets = [b for b in sample_bets if b.status == BetStatus.PENDING]
        mock_bet_repository.get_by_status.return_value = pending_bets
        
        # Act
        result = await bet_service.get_bets_by_status(BetStatus.PENDING)
        
        # Assert
        assert len(result) == len(pending_bets)
        assert all(bet.status == BetStatus.PENDING for bet in result)
        mock_bet_repository.get_by_status.assert_called_once_with(BetStatus.PENDING)
    
    @pytest.mark.asyncio
    async def test_create_bet_successful(self, bet_service, mock_event_repository, 
                                         mock_bet_repository, sample_events):
        """
        GIVEN a valid event and bet request
        WHEN create_bet() is called
        THEN it should create and return a new bet
        """
        # Arrange
        event = sample_events[0]  # Active event
        mock_event_repository.get_by_id.return_value = event
        
        bet_request = BetRequest(event_id=event.event_id, amount=Decimal("25.00"))
        created_bet = Bet(
            bet_id=100,
            event_id=event.event_id,
            amount=bet_request.amount,
            status=BetStatus.PENDING,
            created_at=datetime.now()
        )
        mock_bet_repository.create.return_value = created_bet
        
        # Act
        result = await bet_service.create_bet(bet_request)
        
        # Assert
        assert isinstance(result, BetResponse)
        assert result.event_id == bet_request.event_id
        assert result.amount == bet_request.amount
        assert result.status == BetStatus.PENDING
        mock_event_repository.get_by_id.assert_called_once_with(event.event_id)
        mock_bet_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_bet_event_not_found(self, bet_service, mock_event_repository):
        """
        GIVEN an event ID that doesn't exist
        WHEN create_bet() is called
        THEN it should raise EventNotFoundError
        """
        # Arrange
        bet_request = BetRequest(event_id=999, amount=Decimal("25.00"))
        mock_event_repository.get_by_id.side_effect = EventNotFoundError(event_id=999)
        
        # Act & Assert
        with pytest.raises(BetCreationError) as exc_info:
            await bet_service.create_bet(bet_request)
        
        assert "999" in str(exc_info.value)
        mock_event_repository.get_by_id.assert_called_once_with(999)
    
    @pytest.mark.asyncio
    async def test_create_bet_event_finished(self, bet_service, mock_event_repository, sample_events):
        """
        GIVEN an event that is already finished
        WHEN create_bet() is called
        THEN it should raise BetCreationError
        """
        # Arrange
        finished_event = sample_events[1]  # FINISHED_WIN status
        mock_event_repository.get_by_id.return_value = finished_event
        
        bet_request = BetRequest(event_id=finished_event.event_id, amount=Decimal("25.00"))
        
        # Act & Assert
        with pytest.raises(BetCreationError) as exc_info:
            await bet_service.create_bet(bet_request)
        
        assert "finished" in str(exc_info.value).lower()
        mock_event_repository.get_by_id.assert_called_once_with(finished_event.event_id)
    
    @pytest.mark.asyncio
    async def test_create_bet_event_deadline_passed(self, bet_service, mock_event_repository, sample_events):
        """
        GIVEN an event with a deadline that has passed
        WHEN create_bet() is called
        THEN it should raise BetCreationError
        """
        # Arrange
        past_deadline_event = sample_events[2]  # Past deadline
        mock_event_repository.get_by_id.return_value = past_deadline_event
        
        bet_request = BetRequest(event_id=past_deadline_event.event_id, amount=Decimal("25.00"))
        
        # Act & Assert
        with pytest.raises(BetCreationError) as exc_info:
            await bet_service.create_bet(bet_request)
        
        assert "deadline" in str(exc_info.value).lower()
        mock_event_repository.get_by_id.assert_called_once_with(past_deadline_event.event_id)
    
    @pytest.mark.asyncio
    async def test_update_bets_status_win(self, bet_service, mock_bet_repository, mock_event_repository, 
                                          sample_bets, sample_events):
        """
        GIVEN an event that finished with win status
        WHEN update_bets_status() is called
        THEN it should update all pending bets for that event to WON status
        """
        # Arrange
        mock_event_repository.get_all.return_value = sample_events
        
        # Get pending bets for the finished event with win status
        win_event = sample_events[1]  # FINISHED_WIN status
        pending_bets_for_win_event = [b for b in sample_bets if b.event_id == win_event.event_id and b.status == BetStatus.PENDING]
        
        # Set up mock behavior for get_by_event_id
        def get_bets_by_event(event_id):
            if event_id == win_event.event_id:
                return pending_bets_for_win_event
            return []
            
        mock_bet_repository.get_by_event_id.side_effect = get_bets_by_event
        
        # Act
        updated_count = await bet_service.update_bets_status()
        
        # Assert
        assert updated_count == len(pending_bets_for_win_event)
        mock_event_repository.get_all.assert_called_once()
        mock_bet_repository.get_by_event_id.assert_any_call(win_event.event_id)
        
        # Verify update_status was called for each pending bet with WON status
        for bet in pending_bets_for_win_event:
            mock_bet_repository.update_status.assert_any_call(bet.bet_id, BetStatus.WON)
    
    @pytest.mark.asyncio
    async def test_update_bets_status_lose(self, bet_service, mock_bet_repository, mock_event_repository, 
                                           sample_bets, sample_events):
        """
        GIVEN an event that finished with lose status
        WHEN update_bets_status() is called
        THEN it should update all pending bets for that event to LOST status
        """
        # Arrange
        mock_event_repository.get_all.return_value = sample_events
        
        # Get pending bets for the finished event with lose status
        lose_event = sample_events[3]  # FINISHED_LOSE status
        pending_bets_for_lose_event = [b for b in sample_bets if b.event_id == lose_event.event_id and b.status == BetStatus.PENDING]
        
        # Set up mock behavior for get_by_event_id
        def get_bets_by_event(event_id):
            if event_id == lose_event.event_id:
                return pending_bets_for_lose_event
            return []
            
        mock_bet_repository.get_by_event_id.side_effect = get_bets_by_event
        
        # Act
        updated_count = await bet_service.update_bets_status()
        
        # Assert
        assert updated_count == len(pending_bets_for_lose_event)
        mock_event_repository.get_all.assert_called_once()
        mock_bet_repository.get_by_event_id.assert_any_call(lose_event.event_id)
        
        # Verify update_status was called for each pending bet with LOST status
        for bet in pending_bets_for_lose_event:
            mock_bet_repository.update_status.assert_any_call(bet.bet_id, BetStatus.LOST)
    
    @pytest.mark.asyncio
    async def test_update_bets_status_not_finished(self, bet_service, mock_bet_repository, mock_event_repository, sample_events):
        """
        GIVEN only events that are not finished
        WHEN update_bets_status() is called
        THEN it should not update any bets
        """
        # Arrange
        # Create a list with only non-finished events
        non_finished_events = [
            event for event in sample_events 
            if not event.status.is_finished
        ]
        mock_event_repository.get_all.return_value = non_finished_events
        
        # Act
        updated_count = await bet_service.update_bets_status()
        
        # Assert
        assert updated_count == 0
        mock_event_repository.get_all.assert_called_once()
        # Verify that get_by_event_id was never called since no events are finished
        mock_bet_repository.get_by_event_id.assert_not_called()