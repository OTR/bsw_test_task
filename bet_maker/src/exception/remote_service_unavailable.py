from fastapi import HTTPException, status

from src.exception import BaseBetMakerError


class RemoteServiceUnavailable(BaseBetMakerError, HTTPException):
    """Удаленный API сервис недоступен"""

    def __init__(self, error_type: str, message: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": error_type, "message": message}
        )
