from fastapi import status

from src.exception import BaseBetMakerError


class RepositoryError(BaseBetMakerError):
    pass


class BetRepositoryError(RepositoryError):
    pass


class EventRepositoryError(RepositoryError):
    pass


class BetNotFoundError(BetRepositoryError):
    def __init__(self, bet_id: int):
        self.bet_id: int = bet_id
        self.status_code: int = status.HTTP_404_NOT_FOUND
        self.detail: str = f"Ставка с ID {bet_id} не найдена"
        super().__init__(f"Ставка с ID {bet_id} не найдена")


class BetRepositoryConnectionError(BetRepositoryError):
    def __init__(self, source: str, message: str):
        self.source: str = source
        self.message: str = message
        super().__init__(f"Ошибка подключения к {source}: {message}")


class BetCreationError(BetRepositoryError):
    def __init__(self, reason: str, **kwargs):
        self.reason: str = reason
        self.status_code: int = status.HTTP_400_BAD_REQUEST
        if original_exception := kwargs.get("original_exception"):
            if isinstance(original_exception, EventNotFoundError):
                self.status_code: int = status.HTTP_404_NOT_FOUND

        self.detail: str = f"Не удалось создать ставку: {reason}"
        super().__init__(f"Не удалось создать ставку: {reason}")


class EventNotFoundError(EventRepositoryError):
    def __init__(self, event_id: int):
        self.event_id: int = event_id
        super().__init__(f"Событие с ID {event_id} не найдено")


class EventRepositoryConnectionError(EventRepositoryError):
    def __init__(self, source: str, message: str):
        self.source: str = source
        self.message: str = message
        super().__init__(f"Ошибка подключения к {source}: {message}")
