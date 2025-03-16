from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List

from src.domain.entity import Bet, BetRequest, BetResponse, Event
from src.domain.repository import BaseBetRepository, BaseEventRepository
from src.domain.vo import BetStatus
from src.exception import BetCreationError, EventNotFoundError


@dataclass
class BetService:
    bet_repository: BaseBetRepository
    event_repository: BaseEventRepository

    async def get_all_bets(self) -> List[BetResponse]:
        """
        Получение всех ставок.
        
        Returns:
            Список объектов BetResponse
        """
        bets: List[Bet] = await self.bet_repository.get_all()
        return [BetResponse.model_validate(bet) for bet in bets]
    
    async def get_bet_by_id(self, bet_id: int) -> BetResponse:
        """
        Получение ставки по ID.
        
        Args:
            bet_id: Уникальный идентификатор ставки
            
        Returns:
            Объект BetResponse для найденной ставки
            
        Raises:
            BetNotFoundError: Если ставка с указанным ID не существует
        """
        bet: Bet = await self.bet_repository.get_by_id(bet_id)
        return BetResponse.model_validate(bet)
    
    async def get_bets_by_event(self, event_id: int) -> List[BetResponse]:
        """
        Получение всех ставок для указанного события.
        
        Args:
            event_id: ID события
            
        Returns:
            Список объектов BetResponse для данного события
        """
        bets: List[Bet] = await self.bet_repository.get_by_event_id(event_id)
        return [BetResponse.model_validate(bet) for bet in bets]
    
    async def get_bets_by_status(self, status: BetStatus) -> List[BetResponse]:
        """
        Получение ставок с определенным статусом.
        
        Args:
            status: Статус для фильтрации
            
        Returns:
            Список объектов BetResponse с указанным статусом
        """
        bets: List[Bet] = await self.bet_repository.get_by_status(status)
        return [BetResponse.model_validate(bet) for bet in bets]
    
    async def create_bet(self, bet_request: BetRequest) -> BetResponse:
        """
        Создание новой ставки на событие.
        
        Args:
            bet_request: Запрос на создание ставки с ID события и суммой
            
        Returns:
            Объект BetResponse для созданной ставки
            
        Raises:
            BetCreationError: Если ставка не может быть создана
        """
        event_id: int = bet_request.event_id
        amount: Decimal = bet_request.amount
        
        try:
            event: Event = await self.event_repository.get_by_id(event_id)
        except EventNotFoundError as e:
            raise BetCreationError(f"Невозможно создать ставку: {str(e)}")
            
        if not event.status.is_active:
            raise BetCreationError(
                f"Невозможно создать ставку: Событие с ID {event_id} уже завершено"
            )

        current_time: int = int(datetime.now().timestamp())
        if event.deadline < current_time:
            raise BetCreationError(
                f"Невозможно создать ставку: Срок события с ID {event_id} истек"
            )
        
        bet = Bet(
            bet_id=0,
            event_id=event_id,
            amount=amount,
            status=BetStatus.PENDING,
            created_at=datetime.now()
        )
        
        created_bet: Bet = await self.bet_repository.create(bet)
        return BetResponse.model_validate(created_bet)

    async def update_bets_status(self) -> int:
        """
        Обновление статусов всех ожидающих ставок на основе завершенных событий.
        
        Returns:
            Количество обновленных ставок
        """
        all_events: List[Event] = await self.event_repository.get_all()
        
        finished_events = {
            e.event_id: e.status for e in all_events 
            if e.status.is_finished
        }
        
        if not finished_events:
            return 0
        
        updated_count: int = 0
        for event_id, event_status in finished_events.items():
            bets: List[Bet] = await self.bet_repository.get_by_event_id(event_id)
            pending_bets = [bet for bet in bets if bet.status == BetStatus.PENDING]
            
            # TODO: bulk update status to avoid N+1 queries
            for bet in pending_bets:
                new_status = BetStatus.from_event_state(str(event_status))
                if new_status != BetStatus.PENDING:
                    await self.bet_repository.update_status(bet.bet_id, new_status)
                    updated_count += 1

        return updated_count
