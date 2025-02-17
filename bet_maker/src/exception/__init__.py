from src.exception.base_bet_maker_error import BaseBetMakerError
from src.exception.remote_service_unavailable import RemoteServiceUnavailable
from src.exception.event_by_id_not_found import EventByIdNotFound
from src.exception.event_repository_connection_error import EventRepositoryConnectionError
from src.exception.repository_errors import (
    RepositoryError,
    BetRepositoryError,
    EventRepositoryError,
    BetNotFoundError,
    BetRepositoryConnectionError,
    BetCreationError,
    EventNotFoundError,
)

__all__ = (
    "BaseBetMakerError",
    "RemoteServiceUnavailable",
    "EventByIdNotFound",
    "EventRepositoryConnectionError",
    "RepositoryError",
    "BetRepositoryError",
    "EventRepositoryError",
    "BetNotFoundError",
    "BetRepositoryConnectionError", 
    "BetCreationError",
    "EventNotFoundError",
)
