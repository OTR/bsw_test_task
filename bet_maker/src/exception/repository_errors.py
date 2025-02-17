from src.exception import BaseBetMakerError


class RepositoryError(BaseBetMakerError):
    """Base exception for all repository-related errors"""
    pass


class BetRepositoryError(RepositoryError):
    """Base exception for all bet repository-related errors"""
    pass


class EventRepositoryError(RepositoryError):
    """Base exception for all event repository-related errors"""
    pass


class BetNotFoundError(BetRepositoryError):
    """Raised when a bet is not found in the repository"""
    def __init__(self, bet_id: int):
        self.bet_id: int = bet_id
        super().__init__(f"Bet with ID {bet_id} not found")


class BetRepositoryConnectionError(BetRepositoryError):
    """Raised when there are connection issues with the bet data source"""
    def __init__(self, source: str, message: str):
        self.source: str = source
        self.message: str = message
        super().__init__(f"Connection error to {source}: {message}")


class BetCreationError(BetRepositoryError):
    """Raised when a bet could not be created in the repository"""
    def __init__(self, reason: str):
        self.reason: str = reason
        super().__init__(f"Failed to create bet: {reason}")


class EventNotFoundError(EventRepositoryError):
    """Raised when an event is not found in the repository"""
    def __init__(self, event_id: int):
        self.event_id: int = event_id
        super().__init__(f"Event with ID {event_id} not found")


class EventRepositoryConnectionError(EventRepositoryError):
    """Raised when there are connection issues with the event source"""
    def __init__(self, source: str, message: str):
        self.source: str = source
        self.message: str = message
        super().__init__(f"Connection error to {source}: {message}")
