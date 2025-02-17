from fastapi import HTTPException, status

from src.exception import BaseBetMakerError


class EventRepositoryConnectionError(BaseBetMakerError, HTTPException):
    """Raised when there are connection issues with the event source"""

    def __init__(self, source: str, message: str):
        self.source: str = source
        self.message: str = message
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Event Repository Connection Error",
                "message": f"Connection error to {source}: {message}",
                "source": source,
                "details": message
            }
        )
