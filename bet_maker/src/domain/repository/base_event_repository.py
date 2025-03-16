from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from src.domain.entity import Event
from src.domain.vo import EventStatus


class BaseEventRepository(ABC):
    
    @abstractmethod
    async def get_all(self) -> List[Event]:
        """
        Получение всех событий.
        
        Returns:
            Список событий
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к источнику данных
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, event_id: int) -> Event:
        """
        Получение события по ID.
        
        Args:
            event_id: Идентификатор события
            
        Returns:
            Событие, если найдено
            
        Raises:
            EventNotFoundError: Если событие с указанным ID не найдено
            EventRepositoryConnectionError: При ошибке подключения к источнику данных
        """
        pass
    
    @abstractmethod
    async def get_active_events(self) -> List[Event]:
        """
        Получение активных событий.
        
        Returns:
            Список активных событий
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к источнику данных
        """
        pass
    
    @abstractmethod
    async def filter_events(
        self,
        status: Optional[EventStatus] = None,
        deadline_before: Optional[datetime] = None,
        deadline_after: Optional[datetime] = None,
    ) -> List[Event]:
        """
        Получение событий по фильтрам.
        
        Args:
            status: Фильтр по статусу
            deadline_before: Только события с дедлайном до этого времени
            deadline_after: Только события с дедлайном после этого времени
            
        Returns:
            Список событий, соответствующих фильтрам
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к источнику данных
        """
        pass
    
    @abstractmethod
    async def exists(self, event_id: int) -> bool:
        """
        Проверка существования события.
        
        Args:
            event_id: ID события для проверки
            
        Returns:
            True если событие существует, False в противном случае
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к источнику данных
        """
        pass
