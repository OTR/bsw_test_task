from dataclasses import dataclass
from typing import List

from src.domain.entity import Event
from src.domain.repository import BaseEventRepository
from src.domain.vo import EventStatus


@dataclass
class EventService:
    repository: BaseEventRepository

    async def get_all_events(self) -> List[Event]:
        """
        Получение всех событий.

        Returns:
            List[Event]: Все события
        """
        return await self.repository.get_all()

    async def get_active_events(self) -> List[Event]:
        """
        Получение активных событий для ставок.
        
        Событие считается активным, если:
        1. Статус NEW (не завершено)
        2. Срок не истек
        
        Returns:
            List[Event]: Список активных событий
        """
        return await self.repository.get_active_events()

    async def get_event(self, event_id: int) -> Event:
        """
        Получение события по его ID.

        Args:
            event_id: Уникальный идентификатор события

        Returns:
            Event: Запрошенное событие

        Raises:
            EventNotFoundError: Если событие с указанным ID не найдено
        """
        return await self.repository.get_by_id(event_id)

    async def create_event(self, event: Event) -> Event:
        """
        Создание нового события для ставок.
        
        Args:
            event: Событие для создания
            
        Returns:
            Event: Созданное событие
            
        Raises:
            EventAlreadyExistsError: Если событие с указанным ID уже существует
            InvalidEventDeadlineError: Если срок события не в будущем
        """
        return await self.repository.create(event)  # TODO: implement

    async def update_event(self, event: Event) -> Event:
        """
        Обновление существующего события.
        
        Args:
            event: Событие с обновленными данными
            
        Returns:
            Event: Обновленное событие
            
        Raises:
            EventNotFoundError: Если событие с указанным ID не найдено
            InvalidEventDeadlineError: Если срок события не в будущем
        """
        return await self.repository.update(event)  # TODO: Implement

    async def finish_event(self, event_id: int, first_team_won: bool) -> Event:
        """
        Отметить событие как завершенное с указанным результатом.

        Args:
            event_id: ID события для завершения
            first_team_won: True если первая команда выиграла, False если вторая

        Returns:
            Event: Обновленное событие

        Raises:
            EventNotFoundError: Если событие с указанным ID не найдено
            ValueError: Если событие уже завершено
        """
        event = await self.repository.get_by_id(event_id)
        if event.is_finished:
            raise ValueError(f"Событие {event_id} уже завершено")

        new_status = EventStatus.FINISHED_WIN if first_team_won else EventStatus.FINISHED_LOSE
        event.status = new_status

        return await self.repository.update(event)  # TODO: Implement

    async def event_exists(self, event_id: int) -> bool:
        """
        Проверка существования события.
        
        Args:
            event_id: ID проверяемого события
            
        Returns:
            bool: True если событие существует, False в противном случае
        """
        return await self.repository.exists(event_id)
