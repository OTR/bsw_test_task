import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from src.infra.repository import SQLAlchemyBetRepository
from src.domain.entity import BetRequest, BetResponse
from src.domain.vo import BetStatus
from src.exception import BetNotFoundError, BetCreationError


class AsyncMockResult:
    def __init__(self, return_value):
        self.return_value = return_value
    
    def scalars(self):
        return self

    def all(self):
        return self.return_value
    
    def scalar_one(self):
        return self.return_value
    
    def scalar_one_or_none(self):
        return self.return_value


@pytest.mark.asyncio
async def test_get_all_bets(sample_bet_models):
    mock_session = MagicMock()
    mock_result = AsyncMockResult(sample_bet_models)
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    bets = await repository.get_all()

    assert len(bets) == len(sample_bet_models)
    for bet, model in zip(bets, sample_bet_models):
        assert bet.bet_id == model.bet_id
        assert bet.amount == model.amount


@pytest.mark.asyncio
async def test_get_bet_by_id(sample_bet_models):
    mock_session = MagicMock()
    mock_result = AsyncMockResult(sample_bet_models[0])
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    bet = await repository.get_by_id(sample_bet_models[0].bet_id)

    assert bet.bet_id == sample_bet_models[0].bet_id


@pytest.mark.asyncio
async def test_get_by_id_not_found():
    mock_session = MagicMock()
    mock_result = AsyncMockResult(None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    with pytest.raises(BetNotFoundError):
        await repository.get_by_id(9999)


@pytest.mark.asyncio
async def test_create_bet(sample_bets):
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    with patch.object(SQLAlchemyBetRepository, '_to_domain_entity', return_value=sample_bets[0]):
        repository = SQLAlchemyBetRepository(session=mock_session)

        created_bet = await repository.create(sample_bets[0])

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()
        assert created_bet.bet_id == sample_bets[0].bet_id


@pytest.mark.asyncio
async def test_create_bet_raises_creation_error(sample_bets):
    mock_session = MagicMock()
    mock_session.add = MagicMock(side_effect=SQLAlchemyError("DB error"))
    mock_session.rollback = AsyncMock()
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    with pytest.raises(BetCreationError):
        await repository.create(sample_bets[0])
    
    mock_session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_bet_status(sample_bet_models):
    mock_session = MagicMock()
    first_result = AsyncMockResult(sample_bet_models[0])
    update_result = AsyncMockResult(None)
    third_result = AsyncMockResult(sample_bet_models[0])
    
    mock_session.execute = AsyncMock()
    mock_session.execute.side_effect = [first_result, update_result, third_result]
    mock_session.commit = AsyncMock()
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    updated_bet = await repository.update_status(sample_bet_models[0].bet_id, BetStatus.WON)

    assert updated_bet is not None
    assert mock_session.execute.await_count == 3
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_status_bet_not_found():
    mock_session = MagicMock()
    mock_result = AsyncMockResult(None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    with pytest.raises(BetNotFoundError):
        await repository.update_status(9999, BetStatus.WON)


@pytest.mark.asyncio
async def test_filter_bets(sample_bet_models):
    mock_session = MagicMock()
    mock_result = AsyncMockResult(sample_bet_models)
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    bets = await repository.filter_bets(event_id=sample_bet_models[0].event_id)

    assert len(bets) == len(sample_bet_models)
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_exists_bet(sample_bet_models):
    mock_session = MagicMock()
    mock_result = AsyncMockResult(sample_bet_models[0])
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    exists = await repository.exists(sample_bet_models[0].bet_id)

    assert exists
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_exists_bet_not_found():
    mock_session = MagicMock()
    mock_result = AsyncMockResult(None)
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)

    exists = await repository.exists(9999)

    assert not exists
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_bets(sample_bets):
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    
    repository = SQLAlchemyBetRepository(session=mock_session)
    
    await repository.update_bets(sample_bets)
    
    assert mock_session.execute.await_count == len(sample_bets)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_save():
    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    repository = SQLAlchemyBetRepository(session=mock_session)
    
    bet_request = BetRequest(
        event_id=101,
        amount=Decimal("100.00")
    )
    
    with patch('src.domain.entity.bet.BetResponse.model_validate', return_value=BetResponse(
        bet_id=1,
        event_id=101,
        amount=Decimal("100.00"),
        status=BetStatus.PENDING,
        created_at=datetime.now()
    )):
        result = await repository.save(bet_request)
    
    assert result is not None
    assert result.event_id == bet_request.event_id
    assert result.amount == bet_request.amount
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_pending_bets(sample_bet_models):
    mock_session = MagicMock()
    pending_models = [m for m in sample_bet_models if m.status == BetStatus.PENDING]
    mock_result = AsyncMockResult(pending_models)
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)
    
    with patch('src.domain.entity.bet.BetResponse.model_validate', 
               side_effect=lambda model, **kwargs: BetResponse(
                   bet_id=model.bet_id,
                   event_id=model.event_id,
                   amount=model.amount,
                   status=model.status,
                   created_at=model.created_at
               )):
        pending_bets = await repository.get_pending_bets()
    
    assert len(pending_bets) == len(pending_models)
    for bet in pending_bets:
        assert bet.status == BetStatus.PENDING
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_bets_with_limit(sample_bet_models):
    mock_session = MagicMock()
    mock_result = AsyncMockResult(sample_bet_models[:2])  
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    repository = SQLAlchemyBetRepository(session=mock_session)
    
    with patch('src.domain.entity.bet.BetResponse.model_validate', 
               side_effect=lambda model, **kwargs: BetResponse(
                   bet_id=model.bet_id,
                   event_id=model.event_id,
                   amount=model.amount,
                   status=model.status,
                   created_at=model.created_at
               )):
        bets = await repository.get_all_bets(limit=2)
    
    assert len(bets) == 2
    mock_session.execute.assert_awaited_once()