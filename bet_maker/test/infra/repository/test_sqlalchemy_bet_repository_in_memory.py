import pytest
from decimal import Decimal

from src.infra.repository import SQLAlchemyBetRepository
from src.domain.entity import Bet, BetRequest
from src.domain.vo import BetStatus
from src.exception import BetNotFoundError


@pytest.mark.asyncio
async def test_get_all_bets(db_session, sample_bet_models):
    async with db_session as session:
        for bet_model in sample_bet_models:
            session.add(bet_model)
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)

    bets = await repository.get_all()

    assert len(bets) == len(sample_bet_models)
    bet_ids = {bet.bet_id for bet in bets}
    model_ids = {model.bet_id for model in sample_bet_models}
    assert bet_ids == model_ids


@pytest.mark.asyncio
async def test_get_bet_by_id(db_session, sample_bet_models):
    async with db_session as session:
        session.add(sample_bet_models[0])
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)

    bet = await repository.get_by_id(sample_bet_models[0].bet_id)

    assert bet.bet_id == sample_bet_models[0].bet_id
    assert str(bet.event_id) == str(sample_bet_models[0].event_id)
    assert bet.amount == sample_bet_models[0].amount
    assert bet.status == sample_bet_models[0].status


@pytest.mark.asyncio
async def test_get_bet_by_id_not_found(db_session):
    async with db_session as session:
        repository = SQLAlchemyBetRepository(session=session)

    with pytest.raises(BetNotFoundError):
        await repository.get_by_id(9999)


@pytest.mark.asyncio
async def test_create_bet(db_session, sample_bets):
    async with db_session as session:
        repository = SQLAlchemyBetRepository(session=session)

    created_bet = await repository.create(sample_bets[0])

    assert str(created_bet.event_id) == str(sample_bets[0].event_id)
    assert created_bet.amount == sample_bets[0].amount
    assert created_bet.status == sample_bets[0].status
    
    db_bet = await repository.get_by_id(created_bet.bet_id)
    assert db_bet.bet_id == created_bet.bet_id


@pytest.mark.asyncio
async def test_update_bet_status(db_session, sample_bet_models):
    async with db_session as session:
        session.add(sample_bet_models[0])
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)

    updated_bet = await repository.update_status(sample_bet_models[0].bet_id, BetStatus.WON)

    assert updated_bet.status == BetStatus.WON
    
    db_bet = await repository.get_by_id(sample_bet_models[0].bet_id)
    assert db_bet.status == BetStatus.WON


@pytest.mark.asyncio
async def test_filter_bets(db_session, sample_bet_models):
    async with db_session as session:
        for bet_model in sample_bet_models:
            session.add(bet_model)
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)
    target_event_id = sample_bet_models[0].event_id
    expected_count = sum(1 for m in sample_bet_models if m.event_id == target_event_id)

    bets = await repository.filter_bets(event_id=target_event_id)

    assert len(bets) == expected_count
    for bet in bets:
        assert str(bet.event_id) == str(target_event_id)


@pytest.mark.asyncio
async def test_filter_bets_by_status(db_session, sample_bet_models):
    async with db_session as session:
        for bet_model in sample_bet_models:
            session.add(bet_model)
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)
    target_status = BetStatus.PENDING
    expected_count = sum(1 for m in sample_bet_models if m.status == target_status)

    bets = await repository.filter_bets(status=target_status)

    assert len(bets) == expected_count
    for bet in bets:
        assert bet.status == target_status


@pytest.mark.asyncio
async def test_exists_bet(db_session, sample_bet_models):
    async with db_session as session:
        session.add(sample_bet_models[0])
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)

    exists = await repository.exists(sample_bet_models[0].bet_id)

    assert exists is True


@pytest.mark.asyncio
async def test_exists_bet_not_found(db_session):
    async with db_session as session:
        repository = SQLAlchemyBetRepository(session=session)

    exists = await repository.exists(9999)

    assert exists is False


@pytest.mark.asyncio
async def test_update_bets(db_session, sample_bet_models):
    async with db_session as session:
        for bet_model in sample_bet_models:
            session.add(bet_model)
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)
    
    updated_bets = [
        Bet(bet_id=sample_bet_models[0].bet_id, event_id=sample_bet_models[0].event_id, amount=sample_bet_models[0].amount, status=BetStatus.WON, created_at=sample_bet_models[0].created_at),
        Bet(bet_id=sample_bet_models[1].bet_id, event_id=sample_bet_models[1].event_id, amount=sample_bet_models[1].amount, status=BetStatus.LOST, created_at=sample_bet_models[1].created_at)
    ]

    await repository.update_bets(updated_bets)

    bet1 = await repository.get_by_id(updated_bets[0].bet_id)
    bet2 = await repository.get_by_id(updated_bets[1].bet_id)
    
    assert bet1.status == BetStatus.WON
    assert bet2.status == BetStatus.LOST


@pytest.mark.asyncio
async def test_save(db_session):
    async with db_session as session:
        repository = SQLAlchemyBetRepository(session=session)
        bet_request = BetRequest(
            event_id=101,
            amount=Decimal("100.00")
        )

    bet_response = await repository.save(bet_request)

    assert bet_response is not None
    assert str(bet_response.event_id) == str(bet_request.event_id)
    assert bet_response.amount == bet_request.amount
    assert bet_response.status == BetStatus.PENDING


@pytest.mark.asyncio
async def test_get_pending_bets(db_session, sample_bet_models):
    async with db_session as session:
        for bet_model in sample_bet_models:
            session.add(bet_model)
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)
    expected_count = sum(1 for m in sample_bet_models if m.status == BetStatus.PENDING)

    pending_bets = await repository.get_pending_bets()

    assert len(pending_bets) == expected_count
    for bet in pending_bets:
        assert bet.status == BetStatus.PENDING


@pytest.mark.asyncio
async def test_get_all_bets_with_limit(db_session, sample_bet_models):
    async with db_session as session:
        for bet_model in sample_bet_models:
            session.add(bet_model)
        await session.commit()
    
    repository = SQLAlchemyBetRepository(session=session)
    limit = 2

    bets = await repository.get_all_bets(limit=limit)

    assert len(bets) <= limit