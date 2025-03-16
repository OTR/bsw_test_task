from abc import ABC, abstractmethod
from typing import List

from src.domain.entity import Event
from src.domain.vo import EventStatus

class BaseEventRepository(ABC):

    @abstractmethod
    async def get_all(self) -> List[Event]:
        """
        Получение всех событий.

        Returns:
            List[Event]: Список всех событий в репозитории
        """
        raise NotImplementedError

    @abstractmethod
    async def get_active_events(self) -> List[Event]:
        """
        Получение активных событий.
        
        Событие считается активным, если:
        1. Статус NEW
        2. Срок не истек
        
        Returns:
            List[Event]: Список активных событий
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, event_id: int) -> Event:
        """
        Получение события по ID.

        Args:
            event_id: Идентификатор события

        Returns:
            Event: Найденное событие

        Raises:
            EventNotFoundError: Если событие с указанным ID не найдено
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, event: Event) -> Event:
        """
        Создание нового события.

        Args:
            event: Сущность события для создания

        Returns:
            Event: Созданное событие

        Raises:
            EventAlreadyExistsError: Если событие с таким ID уже существует
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, event: Event) -> Event:
        """
        Обновление существующего события.

        Args:
            event: Сущность события с обновленными данными

        Returns:
            Event: Обновленное событие

        Raises:
            EventNotFoundError: Если событие с указанным ID не найдено
        """
        raise NotImplementedError

    @abstractmethod
    async def update_status(self, event_id: int, new_status: EventStatus) -> Event:
        """
        Обновление статуса события.

        Args:
            event_id: ID события для обновления
            new_status: Новый статус

        Returns:
            Event: Обновленное событие

        Raises:
            EventNotFoundError: Если событие с указанным ID не найдено
        """
        raise NotImplementedError

    @abstractmethod
    async def exists(self, event_id: int) -> bool:
        """
        Проверка существования события.

        Args:
            event_id: ID события для проверки

        Returns:
            bool: True если событие существует, False в противном случае
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """
        Удаление всех событий из репозитория.
        """
        raise NotImplementedError
