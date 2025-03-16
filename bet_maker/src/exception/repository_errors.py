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
        super().__init__(f"Ставка с ID {bet_id} не найдена")


class BetRepositoryConnectionError(BetRepositoryError):
    def __init__(self, source: str, message: str):
        self.source: str = source
        self.message: str = message
        super().__init__(f"Ошибка подключения к {source}: {message}")


class BetCreationError(BetRepositoryError):
    def __init__(self, reason: str):
        self.reason: str = reason
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
