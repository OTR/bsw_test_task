from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.service import BetService
from src.domain.entity import Bet, BetRequest, BetResponse, Event
from src.domain.vo import BetStatus, EventStatus
from src.exception import BetCreationError, BetNotFoundError, EventNotFoundError


@pytest.fixture
def mock_bet_repo():
    return AsyncMock()


@pytest.fixture
def mock_event_repo():
    return AsyncMock()


@pytest.fixture
def bet_service(mock_bet_repo, mock_event_repo):
    return BetService(bet_repository=mock_bet_repo, event_repository=mock_event_repo)


@pytest.fixture
def sample_events():
    now = datetime.now()
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    return [
        Event(event_id=1, coefficient=Decimal("1.50"), deadline=int(future.timestamp()), status=EventStatus.NEW),
        Event(event_id=2, coefficient=Decimal("2.00"), deadline=int(future.timestamp()), status=EventStatus.FINISHED_WIN),
        Event(event_id=3, coefficient=Decimal("3.00"), deadline=int(past.timestamp()), status=EventStatus.NEW),
        Event(event_id=4, coefficient=Decimal("4.00"), deadline=int(past.timestamp()), status=EventStatus.FINISHED_LOSE),
    ]


@pytest.fixture
def sample_bets():
    now = datetime.now()
    return [
        Bet(bet_id=1, event_id=1, amount=Decimal("10.00"), status=BetStatus.PENDING, created_at=now),
        Bet(bet_id=2, event_id=2, amount=Decimal("20.00"), status=BetStatus.PENDING, created_at=now),
        Bet(bet_id=3, event_id=3, amount=Decimal("30.00"), status=BetStatus.PENDING, created_at=now),
        Bet(bet_id=4, event_id=4, amount=Decimal("40.00"), status=BetStatus.PENDING, created_at=now),
    ]


class TestBetService:
    @pytest.mark.asyncio
    async def test_get_all_bets(self, bet_service, mock_bet_repo, sample_bets):
        mock_bet_repo.get_all.return_value = sample_bets
        result = await bet_service.get_all_bets()
        assert len(result) == len(sample_bets)
        assert all(isinstance(bet, BetResponse) for bet in result)
        mock_bet_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_bet_by_id(self, bet_service, mock_bet_repo, sample_bets):
        bet = sample_bets[0]
        mock_bet_repo.get_by_id.return_value = bet
        result = await bet_service.get_bet_by_id(1)
        assert isinstance(result, BetResponse)
        assert result.bet_id == bet.bet_id
        mock_bet_repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_bet_by_id_not_found(self, bet_service, mock_bet_repo):
        mock_bet_repo.get_by_id.side_effect = BetNotFoundError(bet_id=999)
        with pytest.raises(BetNotFoundError) as exc_info:
            await bet_service.get_bet_by_id(999)
        assert "999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_bets_by_event(self, bet_service, mock_bet_repo, sample_bets):
        event_bets = [b for b in sample_bets if b.event_id == 1]
        mock_bet_repo.get_by_event_id.return_value = event_bets
        result = await bet_service.get_bets_by_event(1)
        assert len(result) == len(event_bets)
        assert all(bet.event_id == 1 for bet in result)
        mock_bet_repo.get_by_event_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_bets_by_status(self, bet_service, mock_bet_repo, sample_bets):
        pending_bets = [b for b in sample_bets if b.status == BetStatus.PENDING]
        mock_bet_repo.get_by_status.return_value = pending_bets
        result = await bet_service.get_bets_by_status(BetStatus.PENDING)
        assert len(result) == len(pending_bets)
        assert all(bet.status == BetStatus.PENDING for bet in result)
        mock_bet_repo.get_by_status.assert_called_once_with(BetStatus.PENDING)

    @pytest.mark.asyncio
    async def test_create_bet_successful(self, bet_service, mock_event_repo, mock_bet_repo, sample_events):
        event = sample_events[0]
        mock_event_repo.get_by_id.return_value = event
        bet_request = BetRequest(event_id=event.event_id, amount=Decimal("25.00"))
        created_bet = Bet(bet_id=100, event_id=event.event_id, amount=bet_request.amount, status=BetStatus.PENDING, created_at=datetime.now())
        mock_bet_repo.create.return_value = created_bet
        result = await bet_service.create_bet(bet_request)
        assert isinstance(result, BetResponse)
        assert result.event_id == bet_request.event_id
        assert result.amount == bet_request.amount
        assert result.status == BetStatus.PENDING
        mock_event_repo.get_by_id.assert_called_once_with(event.event_id)
        mock_bet_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bet_event_not_found(self, bet_service, mock_event_repo):
        bet_request = BetRequest(event_id=999, amount=Decimal("25.00"))
        mock_event_repo.get_by_id.side_effect = EventNotFoundError(event_id=999)
        with pytest.raises(BetCreationError) as exc_info:
            await bet_service.create_bet(bet_request)
        assert "999" in str(exc_info.value)
        mock_event_repo.get_by_id.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_create_bet_event_finished(self, bet_service, mock_event_repo, sample_events):
        finished_event = sample_events[1]
        mock_event_repo.get_by_id.return_value = finished_event
        bet_request = BetRequest(event_id=finished_event.event_id, amount=Decimal("25.00"))
        with pytest.raises(BetCreationError) as exc_info:
            await bet_service.create_bet(bet_request)
        assert "завершено" in str(exc_info.value).lower()
        mock_event_repo.get_by_id.assert_called_once_with(finished_event.event_id)

    @pytest.mark.asyncio
    async def test_create_bet_event_deadline_passed(self, bet_service, mock_event_repo, sample_events):
        past_deadline_event = sample_events[2]
        mock_event_repo.get_by_id.return_value = past_deadline_event
        bet_request = BetRequest(event_id=past_deadline_event.event_id, amount=Decimal("25.00"))
        with pytest.raises(BetCreationError) as exc_info:
            await bet_service.create_bet(bet_request)
        assert "истек" in str(exc_info.value).lower()
        mock_event_repo.get_by_id.assert_called_once_with(past_deadline_event.event_id)

    @pytest.mark.asyncio
    async def test_update_bets_status_win(self, bet_service, mock_bet_repo, mock_event_repo, sample_bets, sample_events):
        mock_event_repo.get_all.return_value = sample_events
        win_event = sample_events[1]
        pending_bets_for_win_event = [b for b in sample_bets if b.event_id == win_event.event_id and b.status == BetStatus.PENDING]

        def get_bets_by_event(event_id):
            return pending_bets_for_win_event if event_id == win_event.event_id else []

        mock_bet_repo.get_by_event_id.side_effect = get_bets_by_event
        updated_count = await bet_service.update_bets_status()
        assert updated_count == len(pending_bets_for_win_event)
        mock_event_repo.get_all.assert_called_once()
        mock_bet_repo.get_by_event_id.assert_any_call(win_event.event_id)
