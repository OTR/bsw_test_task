from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.exception import (
    LineProviderError,
    EventNotFoundError,
    EventAlreadyExistsError,
    InvalidEventDeadlineError,
)


def create_error_response(status_code: int, message: str, error_type: str) -> Dict[str, Any]:
    """
    Создает стандартный словарь ответа об ошибке.
    
    Args:
        status_code: HTTP код статуса
        message: Сообщение об ошибке
        error_type: Тип ошибки (имя класса)
        
    Returns:
        Словарь с деталями ошибки
    """
    return {
        "error": {
            "status_code": status_code,
            "message": message,
            "error_type": error_type
        }
    }


async def validation_error_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    Обрабатывает ошибки валидации Pydantic.
    Перехватывает доменные исключения во время валидации.
    """
    if exc.raw_errors:
        for error in exc.raw_errors:
            if hasattr(error, 'exc'):
                original_error = error.exc
                if isinstance(original_error, LineProviderError):
                    if isinstance(original_error, InvalidEventDeadlineError):
                        return await invalid_event_deadline_handler(request, original_error)
                    if isinstance(original_error, EventNotFoundError):
                        return await event_not_found_handler(request, original_error)
                    if isinstance(original_error, EventAlreadyExistsError):
                        return await event_already_exists_handler(request, original_error)
                    return await line_provider_error_handler(request, original_error)
            elif isinstance(error, InvalidEventDeadlineError):
                return await invalid_event_deadline_handler(request, error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(exc),
            error_type="ValidationError"
        )
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Обрабатывает ошибки валидации запросов FastAPI.
    
    Перехватывает ошибки валидации на уровне API до их попадания в доменные модели.
    """
    if hasattr(exc, 'raw_errors'):
        for error in exc.raw_errors:
            if hasattr(error, 'exc') and isinstance(error.exc, LineProviderError):
                original_error = error.exc
                if isinstance(original_error, InvalidEventDeadlineError):
                    return await invalid_event_deadline_handler(request, original_error)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(exc),
            error_type="RequestValidationError"
        )
    )


async def event_not_found_handler(
    request: Request,
    exc: EventNotFoundError
) -> JSONResponse:
    """Обрабатывает исключения о ненайденных событиях."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=str(exc),
            error_type="EventNotFound"
        )
    )


async def event_already_exists_handler(
    request: Request,
    exc: EventAlreadyExistsError
) -> JSONResponse:
    """Обрабатывает исключения о существующих событиях."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            message=str(exc),
            error_type="EventAlreadyExists"
        )
    )


async def invalid_event_deadline_handler(
    request: Request,
    exc: InvalidEventDeadlineError
) -> JSONResponse:
    """
    Обрабатывает исключения о неверных сроках событий.
    
    Обрабатывает ошибки валидации сроков событий, которые могут быть отрицательными или не в будущем.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(exc),
            error_type="InvalidEventDeadline"
        )
    )


async def line_provider_error_handler(
    request: Request,
    exc: LineProviderError
) -> JSONResponse:
    """
    Обрабатывает необработанные исключения LineProviderError.
    Это общий обработчик для доменных исключений без специальных обработчиков.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(exc),
            error_type=exc.__class__.__name__
        )
    )


exception_handlers = {
    ValidationError: validation_error_handler,
    RequestValidationError: request_validation_error_handler,
    EventNotFoundError: event_not_found_handler,
    EventAlreadyExistsError: event_already_exists_handler,
    InvalidEventDeadlineError: invalid_event_deadline_handler,
    LineProviderError: line_provider_error_handler,
}


def register_error_handlers(app: FastAPI) -> None:
    """
    Регистрирует все обработчики ошибок в приложении FastAPI.
    
    Args:
        app: Экземпляр приложения FastAPI
    """
    for exception_class, handler in exception_handlers.items():
        app.add_exception_handler(exception_class, handler)
