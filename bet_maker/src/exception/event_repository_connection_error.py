from fastapi import HTTPException, status

from src.exception import BaseBetMakerError


class EventRepositoryConnectionError(BaseBetMakerError, HTTPException):
    """Когда возникают проблемы с подключением к источнику событий"""

    def __init__(self, source: str, message: str):
        self.source: str = source
        self.message: str = message
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Event Repository Connection Error",
                "message": f"Ошибка подключения к {source}: {message}",
                "source": source,
                "details": message
            }
        )
