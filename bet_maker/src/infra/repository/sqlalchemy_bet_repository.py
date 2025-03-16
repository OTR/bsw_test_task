from typing import List, Union, Optional
from datetime import datetime

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.domain.entity import Bet, BetRequest, BetResponse
from src.domain.repository import BaseBetRepository
from src.domain.vo import BetStatus
from src.infra.database.bet_model import BetModel
from src.exception import (
    BetNotFoundError,
    BetRepositoryConnectionError,
    BetCreationError
)


class SQLAlchemyBetRepository(BaseBetRepository):
    
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def get_all(self) -> List[Bet]:
        """
        Получение всех ставок из базы данных.
        
        Returns:
            Список доменных сущностей Bet
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = select(BetModel).order_by(BetModel.created_at.desc())
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось получить ставки: {str(e)}")
    
    async def get_by_id(self, bet_id: Union[int, str]) -> Bet:
        """
        Получение ставки по её уникальному идентификатору.
        
        Args:
            bet_id: Уникальный идентификатор ставки
            
        Returns:
            Доменная сущность Bet, если найдена
            
        Raises:
            BetNotFoundError: Если ставка с указанным ID не существует
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = select(BetModel).where(BetModel.bet_id == bet_id)
            result = await self._session.execute(stmt)
            bet_model = result.scalar_one_or_none()
            
            if bet_model is None:
                raise BetNotFoundError(f"Ставка с ID {bet_id} не найдена")
            
            return self._to_domain_entity(bet_model)
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось получить ставку: {str(e)}")
    
    async def create(self, bet: Bet) -> Bet:
        """
        Создание новой ставки в базе данных.
        
        Args:
            bet: Доменная сущность Bet для создания
            
        Returns:
            Созданная доменная сущность Bet с присвоенным ID
            
        Raises:
            BetCreationError: Если ставку не удалось создать
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            bet_model = self._to_db_model(bet)
            
            self._session.add(bet_model)
            await self._session.commit()
            await self._session.refresh(bet_model)
            
            return self._to_domain_entity(bet_model)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetCreationError(f"Не удалось создать ставку: {str(e)}")
        except Exception as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Непредвиденная ошибка: {str(e)}")
    
    async def get_by_event_id(self, event_id: Union[int, str]) -> List[Bet]:
        """
        Получение всех ставок, связанных с определенным событием.
        
        Args:
            event_id: Уникальный идентификатор события
            
        Returns:
            Список доменных сущностей Bet, связанных с событием
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = select(BetModel).where(BetModel.event_id == str(event_id))
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось получить ставки по ID события: {str(e)}")
    
    async def get_by_status(self, status: BetStatus) -> List[Bet]:
        """
        Получение всех ставок с определенным статусом.
        
        Args:
            status: Статус для фильтрации
            
        Returns:
            Список доменных сущностей Bet с указанным статусом
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = select(BetModel).where(BetModel.status == status)
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось получить ставки по статусу: {str(e)}")
    
    async def update_status(self, bet_id: Union[int, str], new_status: BetStatus) -> Bet:
        """
        Обновление статуса конкретной ставки.
        
        Args:
            bet_id: Уникальный идентификатор обновляемой ставки
            new_status: Новый статус
            
        Returns:
            Обновленная доменная сущность Bet
            
        Raises:
            BetNotFoundError: Если ставка с указанным ID не существует
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            exists = await self.exists(bet_id)
            if not exists:
                raise BetNotFoundError(f"Ставка с ID {bet_id} не найдена")
            
            stmt = (
                update(BetModel)
                .where(BetModel.bet_id == bet_id)
                .values(status=new_status)
            )
            await self._session.execute(stmt)
            
            get_stmt = select(BetModel).where(BetModel.bet_id == bet_id)
            result = await self._session.execute(get_stmt)
            updated_bet = result.scalar_one_or_none()
            
            if updated_bet is None:
                raise BetNotFoundError(f"Ставка с ID {bet_id} не найдена после обновления")
                
            await self._session.commit()
                
            return self._to_domain_entity(updated_bet)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Не удалось обновить статус ставки: {str(e)}")
    
    async def bulk_update_status(self, bet_ids: List[Union[int, str]], new_status: BetStatus) -> int:
        """
        Обновление статуса нескольких ставок за одну операцию.
        
        Args:
            bet_ids: Уникальные идентификаторы ставок для обновления
            new_status: Новый статус
            
        Returns:
            Количество обновленных ставок
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = (
                update(BetModel)
                .where(BetModel.bet_id.in_(bet_ids))
                .values(status=new_status)
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Не удалось обновить статусы ставок: {str(e)}")
    
    async def filter_bets(
        self,
        event_id: Optional[int] = None,
        status: Optional[BetStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Bet]:
        """
        Получение ставок, соответствующих указанным фильтрам.
        
        Args:
            event_id: Фильтр по ID события
            status: Фильтр по статусу ставки
            created_after: Только ставки, созданные после этого времени
            created_before: Только ставки, созданные до этого времени
            
        Returns:
            Список доменных сущностей Bet, соответствующих фильтрам
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            filters = []
            if event_id is not None:
                filters.append(BetModel.event_id == str(event_id))
            
            if status is not None:
                filters.append(BetModel.status == status)
                
            if created_after is not None:
                filters.append(BetModel.created_at >= created_after)
                
            if created_before is not None:
                filters.append(BetModel.created_at <= created_before)
            
            stmt = select(BetModel)
            if filters:
                stmt = stmt.where(and_(*filters))
            
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось отфильтровать ставки: {str(e)}")
    
    async def exists(self, bet_id: int) -> bool:
        """
        Проверка существования ставки с указанным ID.
        
        Args:
            bet_id: Уникальный идентификатор проверяемой ставки
            
        Returns:
            True если ставка существует, False в противном случае
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = select(BetModel.bet_id).where(BetModel.bet_id == bet_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось проверить существование ставки: {str(e)}")
    
    async def update_bets(self, bets: List[Bet]) -> List[Bet]:
        """
        Обновление нескольких ставок за одну операцию.
        
        Args:
            bets: Список сущностей ставок с обновленными значениями
            
        Returns:
            Список обновленных сущностей ставок
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            updated_bets = []
            
            for bet in bets:
                stmt = (
                    update(BetModel)
                    .where(BetModel.bet_id == bet.bet_id)
                    .values(
                        event_id=str(bet.event_id),
                        amount=bet.amount,
                        status=bet.status
                    )
                )
                await self._session.execute(stmt)
                
                updated_bets.append(bet)
            
            await self._session.commit()
            
            return updated_bets
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Не удалось обновить ставки: {str(e)}")
    
    async def save(self, bet_request: BetRequest) -> BetResponse:
        """
        Сохранение новой ставки из BetRequest DTO.
        
        Args:
            bet_request: Данные запроса на создание ставки из API
            
        Returns:
            BetResponse с данными сохраненной ставки
            
        Raises:
            BetCreationError: Если ставку не удалось создать
        """
        try:
            new_bet_model = BetModel(
                event_id=str(bet_request.event_id),
                amount=bet_request.amount,
                status=BetStatus.PENDING
            )
            
            self._session.add(new_bet_model)
            await self._session.commit()
            await self._session.refresh(new_bet_model)
            
            return BetResponse.model_validate(new_bet_model, from_attributes=True)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetCreationError(f"Не удалось сохранить ставку: {str(e)}")
    
    save_bet = save
    
    async def get_pending_bets(self) -> List[BetResponse]:
        """
        Получение всех ставок со статусом `PENDING`.
        
        Returns:
            Список ожидающих ставок
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = select(BetModel).where(BetModel.status == BetStatus.PENDING)
            result = await self._session.execute(stmt)
            pending_bets = result.scalars().all()
            
            return [BetResponse.model_validate(bet, from_attributes=True) for bet in pending_bets]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось получить ожидающие ставки: {str(e)}")
    
    async def get_all_bets(self, limit: int = 100) -> List[BetResponse]:
        """
        Получение всех ставок из базы данных с пагинацией.
        
        Args:
            limit: Максимальное количество возвращаемых ставок
            
        Returns:
            Список ставок до указанного лимита
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к базе данных
        """
        try:
            stmt = select(BetModel).order_by(BetModel.created_at.desc()).limit(limit)
            result = await self._session.execute(stmt)
            bets = result.scalars().all()
            
            return [BetResponse.model_validate(bet, from_attributes=True) for bet in bets]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Не удалось получить все ставки: {str(e)}")
    
    def _to_domain_entity(self, bet_model: BetModel) -> Bet:
        """
        Преобразование модели базы данных в доменную сущность.
        
        Args:
            bet_model: Модель базы данных для преобразования
            
        Returns:
            Соответствующая доменная сущность
        """
        return Bet(
            bet_id=bet_model.bet_id,
            event_id=bet_model.event_id,
            amount=bet_model.amount,
            status=bet_model.status,
            created_at=bet_model.created_at
        )
    
    def _to_db_model(self, bet: Bet) -> BetModel:
        """
        Преобразование доменной сущности в модель базы данных.
        
        Args:
            bet: Доменная сущность для преобразования
            
        Returns:
            Соответствующая модель базы данных
        """
        bet_model = BetModel(
            event_id=bet.event_id,
            amount=bet.amount,
            status=bet.status
        )
        
        if hasattr(bet, 'bet_id') and bet.bet_id is not None:
            bet_model.bet_id = bet.bet_id
        
        if hasattr(bet, 'created_at') and bet.created_at is not None:
            bet_model.created_at = bet.created_at
        
        return bet_model
