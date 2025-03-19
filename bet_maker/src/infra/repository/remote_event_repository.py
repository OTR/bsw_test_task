from datetime import datetime
from typing import Optional, List

from fastapi import status
from httpx import HTTPStatusError

from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventRepositoryConnectionError
from src.infra.http import HTTPClient


class RemoteEventRepository(BaseEventRepository):

    def __init__(self, http_client: HTTPClient):
        """
        Инициализация удаленного репозитория событий.
        
        Args:
            http_client: HTTP клиент для запросов к удаленному сервису
        """
        self.http_client: HTTPClient = http_client

    async def get_all(self) -> List[Event]:
        """
        Получение всех доступных событий из удаленного сервиса.
        
        Returns:
            Список доменных сущностей Event
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к удаленному сервису
        """
        try:
            events: List[Event] = await self.http_client.get_model_list("/api/v1/events", Event)
            return events
        except Exception as err:
            raise EventRepositoryConnectionError(source="remote-line-provider", message=str(err)) from err

    async def get_by_id(self, event_id: int) -> Event:
        """
        Получение события по его уникальному идентификатору.
        
        Args:
            event_id: Уникальный идентификатор события
            
        Returns:
            Доменная сущность Event, если найдена
            
        Raises:
            EventNotFoundError: Если событие с указанным ID не существует
            EventRepositoryConnectionError: При ошибке подключения к удаленному сервису
        """
        try:
            event: Event = await self.http_client.get_model(f"/api/v1/events/{event_id}", Event)
            return event
        except HTTPStatusError as err:
            if err.response.status_code == status.HTTP_404_NOT_FOUND:
                raise EventNotFoundError(event_id=event_id) from err
            raise EventRepositoryConnectionError(source="remote-line-provider", message=str(err)) from err
        except Exception as err:
            raise EventRepositoryConnectionError(source="remote-line-provider", message=str(err)) from err

    async def get_active_events(self, limit: int, offset: int) -> List[Event]:
        """
        Получение всех активных событий.
        Активные события - это те, которые еще не начались и принимают ставки.
        
        Returns:
            Список активных событий
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к удаленному сервису
        """
        all_events: List[Event] = await self.get_all()
        return [event for event in all_events if event.is_active][offset:offset + limit]   

    async def filter_events(
        self,
        status: Optional[EventStatus] = None,
        deadline_before: Optional[datetime] = None,
        deadline_after: Optional[datetime] = None,
    ) -> List[Event]:
        """
        Получение событий, соответствующих указанным фильтрам.
        
        Args:
            status: Фильтр по статусу события
            deadline_before: Только события с дедлайном до этого времени
            deadline_after: Только события с дедлайном после этого времени
            
        Returns:
            Список событий, соответствующих фильтрам
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к удаленному сервису
        """
        all_events: List[Event] = await self.get_all()
        filtered_events: List[Event] = all_events

        if status is not None:
            filtered_events = [event for event in filtered_events if event.status == status]

        if deadline_before is not None:
            before_timestamp: int = int(deadline_before.timestamp())
            filtered_events = [event for event in filtered_events if event.deadline < before_timestamp]

        if deadline_after is not None:
            after_timestamp: int = int(deadline_after.timestamp())
            filtered_events = [event for event in filtered_events if event.deadline > after_timestamp]

        return filtered_events

    async def exists(self, event_id: int) -> bool:
        """
        Проверка существования события с указанным ID.
        
        Args:
            event_id: Уникальный идентификатор проверяемого события
            
        Returns:
            True если событие существует, False в противном случае
            
        Raises:
            EventRepositoryConnectionError: При ошибке подключения к удаленному сервису
        """
        try:
            await self.get_by_id(event_id)
            return True
        except EventNotFoundError:
            return False
