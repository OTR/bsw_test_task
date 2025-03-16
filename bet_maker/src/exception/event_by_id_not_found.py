from fastapi import HTTPException, status

from src.exception import BaseBetMakerError


class EventByIdNotFound(BaseBetMakerError, HTTPException):
    """Когда удаленный API сервис не может найти событие по заданному ID"""

    def __init__(self, error_type: str, message: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": error_type, "message": message}
        )
