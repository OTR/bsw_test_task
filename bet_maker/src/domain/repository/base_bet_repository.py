from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List

from src.domain.entity import Bet
from src.domain.vo import BetStatus


class BaseBetRepository(ABC):

    @abstractmethod
    async def get_all(self, limit: int, offset: int, status: str) -> List[Bet]:
        """
        Получение всех ставок.
        
        Returns:
            Список сущностей Bet
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """

    @abstractmethod
    async def get_by_id(self, bet_id: int) -> Bet:
        """
        Получение ставки по ID.
        
        Args:
            bet_id: Уникальный идентификатор ставки
            
        Returns:
            Сущность Bet, если найдена
            
        Raises:
            BetNotFoundError: Если ставка с указанным ID не найдена
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """

    @abstractmethod
    async def get_by_status(self, status: BetStatus) -> List[Bet]:
        """
        Получение ставок с определенным статусом.
        
        Args:
            status: Статус для фильтрации
            
        Returns:
            Список ставок с указанным статусом
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """

    @abstractmethod
    async def get_by_event_id(self, event_id: int) -> List[Bet]:
        """
        Получение ставок для конкретного события.
        
        Args:
            event_id: ID события
            
        Returns:
            Список ставок для указанного события
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """

    @abstractmethod
    async def create(self, bet: Bet) -> Bet:
        """
        Создание новой ставки.
        
        Args:
            bet: Сущность Bet для создания
            
        Returns:
            Созданная сущность Bet с присвоенным ID
            
        Raises:
            BetCreationError: Если ставка не может быть создана
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """

    @abstractmethod
    async def update_status(self, bet_id: int, new_status: BetStatus) -> Bet:
        """
        Обновление статуса ставки.
        
        Args:
            bet_id: ID ставки для обновления
            new_status: Новый статус
            
        Returns:
            Обновленная сущность Bet
            
        Raises:
            BetNotFoundError: Если ставка с указанным ID не найдена
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """

    @abstractmethod
    async def filter_bets(
        self,
        event_id: Optional[int] = None,
        status: Optional[BetStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Bet]:
        """
        Получение ставок по фильтрам.
        
        Args:
            event_id: Фильтр по ID события
            status: Фильтр по статусу ставки
            created_after: Только ставки, созданные после этого времени
            created_before: Только ставки, созданные до этого времени
            
        Returns:
            Список ставок, соответствующих фильтрам
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """

    @abstractmethod
    async def exists(self, bet_id: int) -> bool:
        """
        Проверка существования ставки с указанным ID.
        
        Args:
            bet_id: ID ставки для проверки
            
        Returns:
            True если ставка существует, False в противном случае
            
        Raises:
            BetRepositoryConnectionError: При ошибке подключения к источнику данных
        """
