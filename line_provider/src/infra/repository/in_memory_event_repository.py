import time
from decimal import Decimal
from typing import List, Dict, Optional

from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus
from src.exception import EventNotFoundError, EventAlreadyExistsError

_EVENTS: Dict[int, Event] = {
    1: Event(event_id=1, coefficient=Decimal("1.20"), deadline=int(time.time()) + 600, status=EventStatus.NEW),
    2: Event(event_id=2, coefficient=Decimal("1.15"), deadline=int(time.time()) + 60, status=EventStatus.NEW),
    3: Event(event_id=3, coefficient=Decimal("1.67"), deadline=int(time.time()) + 90, status=EventStatus.NEW)
}


class InMemoryEventRepository(BaseEventRepository):

    def __init__(self, events: Dict[int, Event] = _EVENTS) -> None:
        self._events: Dict[int, Event] = events

    async def get_all(self) -> List[Event]:
        """
        Получает все события независимо от их статуса или срока.

        Returns:
            List[Event]: Список всех событий в репозитории
        """
        return list(self._events.values())

    async def get_active_events(self) -> List[Event]:
        """
        Получает все активные события (не завершенные и не просроченные).
        
        Событие считается активным, если:
        1. Его статус - NEW
        2. Срок еще не истек
        
        Returns:
            List[Event]: Список активных событий
        """
        return [event for event in self._events.values() if event.is_active]

    async def get_by_id(self, event_id: int) -> Event:
        """
        Получает событие по его ID.

        Args:
            event_id: Уникальный идентификатор события

        Returns:
            Event: Событие, если найдено

        Raises:
            EventNotFoundError: Если событие с указанным ID не существует
        """
        event: Optional[Event] = self._events.get(event_id)
        if not event:
            raise EventNotFoundError(event_id)
        return event

    async def create(self, event: Event) -> Event:
        """
        Создает новое событие в репозитории.

        Args:
            event: Сущность события для создания

        Returns:
            Event: Созданное событие

        Raises:
            EventAlreadyExistsError: Если событие с таким же ID уже существует
        """
        if await self.exists(event.event_id):
            raise EventAlreadyExistsError(event.event_id)

        self._events[event.event_id] = event
        return event

    async def update(self, event: Event) -> Event:
        """
        Обновляет существующее событие в репозитории.

        Args:
            event: Сущность события с обновленными данными

        Returns:
            Event: Обновленное событие

        Raises:
            EventNotFoundError: Если событие с указанным ID не существует
        """
        if not await self.exists(event.event_id):
            raise EventNotFoundError(event.event_id)

        self._events[event.event_id] = event
        return event

    async def update_status(self, event_id: int, new_status: EventStatus) -> Event:
        """
        Обновляет статус события.

        Это специальный метод для изменения статуса события, соответствующий
        принципу специализированных методов репозитория.

        Args:
            event_id: ID события для обновления
            new_status: Новый статус

        Returns:
            Event: Обновленное событие

        Raises:
            EventNotFoundError: Если событие с указанным ID не существует
        """
        event: Event = await self.get_by_id(event_id)
        event.status = new_status
        return event

    async def exists(self, event_id: int) -> bool:
        """
        Проверяет существование события в репозитории.

        Args:
            event_id: ID события для проверки

        Returns:
            bool: True если событие существует, False в противном случае
        """
        return event_id in self._events

    async def clear(self) -> None:
        """
        Удаляет все события из репозитория.
        
        В основном полезно для тестирования.
        """
        self._events.clear()
