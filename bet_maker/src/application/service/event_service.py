from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.domain.repository import BaseEventRepository
from src.domain.entity import Event
from src.domain.vo import EventStatus


@dataclass
class EventService:
    repository: BaseEventRepository

    async def get_all(self) -> List[Event]:
        """
        Получение всех событий.
        
        Returns:
            Список всех объектов Event
            
        Raises:
            EventRepositoryConnectionError: При проблеме соединения с репозиторием
        """
        return await self.repository.get_all()

    async def get_active_events(self) -> List[Event]:
        """
        Получение активных событий, доступных для ставок.
        Событие считается активным, если имеет статус NEW и ещё не завершилось.
        
        Returns:
            Список активных объектов Event
            
        Raises:
            EventRepositoryConnectionError: При проблеме соединения с репозиторием
        """
        return await self.repository.get_active_events()
    
    async def get_events_by_status(self, status: EventStatus) -> List[Event]:
        """
        Получение событий с указанным статусом.
        
        Args:
            status: Статус для фильтрации
            
        Returns:
            Список объектов Event с указанным статусом
            
        Raises:
            EventRepositoryConnectionError: При проблеме соединения с репозиторием
        """
        return await self.repository.filter_events(status=status)
    
    async def get_events_by_deadline(
        self, 
        before: Optional[datetime] = None, 
        after: Optional[datetime] = None
    ) -> List[Event]:
        """
        Получение событий со сроками в указанном временном диапазоне.
        
        Args:
            before: Если указано, включать события со сроками до этого времени
            after: Если указано, включать события со сроками после этого времени
            
        Returns:
            Список объектов Event, соответствующих критериям поиска
            
        Raises:
            EventRepositoryConnectionError: При проблеме соединения с репозиторием
        """
        return await self.repository.filter_events(
            deadline_before=before,
            deadline_after=after
        )
    
    async def get_event_by_id(self, event_id: int) -> Event:
        """
        Получение события по его ID.
        
        Args:
            event_id: Уникальный идентификатор события
            
        Returns:
            Объект Event, если найден
            
        Raises:
            EventNotFoundError: Если событие с указанным ID не существует
            EventRepositoryConnectionError: При проблеме соединения с репозиторием
        """
        return await self.repository.get_by_id(event_id)
