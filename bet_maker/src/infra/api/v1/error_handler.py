from typing import Any, Dict, Optional

from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError


from src.domain.exceptions import (
    DomainError, 
    EventNotFoundError, 
    BetServiceError,
    InsufficientBalanceError,
    InvalidBetAmountError
)

from src.exception import (
    RemoteServiceUnavailable, 
    EventByIdNotFound, 
    EventRepositoryConnectionError,
)


class ErrorResponse:
    """Стандартный формат ответа об ошибке"""
    
    @staticmethod
    def create(
        status_code: int,
        message: str,
        error_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        response = {
            "error": {
                "status_code": status_code,
                "message": message,
                "error_type": error_type
            }
        }
        
        if details:
            response["error"]["details"] = details
            
        return response



async def remote_service_unavailable_handler(
    request: Request,
    exc: RemoteServiceUnavailable
) -> JSONResponse:
    """Обработчик недоступности удаленного сервиса"""
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code,
    )


async def event_id_not_found_handler(
    request: Request,
    exc: EventByIdNotFound
) -> JSONResponse:
    """Обработчик когда событие не найдено в удаленном API"""
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code
    )


async def event_repository_connection_error_handler(
    request: Request,
    exc: EventRepositoryConnectionError
) -> JSONResponse:
    """Обработчик ошибок подключения к репозиторию событий"""
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code
    )


async def domain_error_handler(
    request: Request,
    exc: DomainError
) -> JSONResponse:
    """Общий обработчик доменных ошибок"""
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=str(exc),
            error_type="DomainError"
        ),
        status_code=status.HTTP_400_BAD_REQUEST
    )


async def event_not_found_error_handler(
    request: Request,
    exc: EventNotFoundError
) -> JSONResponse:
    """Обработчик когда событие не найдено в репозитории"""
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_404_NOT_FOUND,
            message=str(exc),
            error_type="EventNotFound",
            details={"event_id": getattr(exc, "event_id", None)}
        ),
        status_code=status.HTTP_404_NOT_FOUND
    )


async def bet_service_error_handler(
    request: Request,
    exc: BetServiceError
) -> JSONResponse:
    """Обработчик ошибок сервиса ставок"""
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(exc),
            error_type="BetServiceError",
            details=getattr(exc, "details", None)
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def insufficient_balance_error_handler(
    request: Request,
    exc: InsufficientBalanceError
) -> JSONResponse:
    """Обработчик ошибки недостаточного баланса"""
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(exc),
            error_type="InsufficientBalance",
            details={
                "user_id": exc.user_id,
                "amount_required": exc.amount_required,
                "amount_available": exc.amount_available
            }
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def invalid_bet_amount_error_handler(
    request: Request,
    exc: InvalidBetAmountError
) -> JSONResponse:
    """Обработчик ошибки недопустимой суммы ставки"""
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=str(exc),
            error_type="InvalidBetAmount",
            details={
                "amount": exc.amount,
                "min_amount": exc.min_amount,
                "max_amount": exc.max_amount
            }
        ),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def response_validation_error_handler(
    request: Request,
    exc: ResponseValidationError
) -> JSONResponse:
    """
    Обработчик ошибок валидации ответа
    """
    error_messages = []
    for error in exc.errors():
        error_messages.append({
            "type": error["type"],
            "location": error["loc"],
            "message": error["msg"],
            "input_type": str(type(error.get("input")))
        })
    
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Сервер столкнулся с ошибкой при обработке ответа",
            error_type="ResponseValidationError",
            details={
                "info": "Вероятно, корутина не была правильно обработана в обработчике",
                "validation_errors": error_messages
            }
        ),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def catch_all_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Обработчик всех необработанных исключений
    """
    error_type = type(exc).__name__
    error_message = str(exc)
    
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Произошла непредвиденная ошибка",
            error_type="ServerError",
            details={
                "error_type": error_type,
                "error_message": error_message
            }
        ),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RemoteServiceUnavailable, remote_service_unavailable_handler)
    app.add_exception_handler(EventByIdNotFound, event_id_not_found_handler)
    app.add_exception_handler(EventRepositoryConnectionError, event_repository_connection_error_handler)
    
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(EventNotFoundError, event_not_found_error_handler)
    app.add_exception_handler(BetServiceError, bet_service_error_handler)
    app.add_exception_handler(InsufficientBalanceError, insufficient_balance_error_handler)
    app.add_exception_handler(InvalidBetAmountError, invalid_bet_amount_error_handler)
    
    app.add_exception_handler(ResponseValidationError, response_validation_error_handler)
    
    app.add_exception_handler(Exception, catch_all_exception_handler)
