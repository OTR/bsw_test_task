from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError
from typing import Any, Dict, Type, Optional

# Import domain exceptions
from src.domain.exceptions import (
    DomainError, 
    EventNotFoundError, 
    BetServiceError,
    InsufficientBalanceError,
    InvalidBetAmountError
)

# Import legacy exceptions for backward compatibility
from src.exception import (
    RemoteServiceUnavailable, 
    EventByIdNotFound, 
    EventRepositoryConnectionError,
)

class ErrorResponse:
    """Standardized error response format"""
    
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


# Legacy exception handlers

async def remote_service_unavailable_handler(
    request: Request,
    exc: RemoteServiceUnavailable
) -> JSONResponse:
    """Custom handler when remote service API is unavailable"""
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code,
    )


async def event_id_not_found_handler(
    request: Request,
    exc: EventByIdNotFound
) -> JSONResponse:
    """Custom handler when event by ID not found in remote API service"""
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code
    )


async def event_repository_connection_error_handler(
    request: Request,
    exc: EventRepositoryConnectionError
) -> JSONResponse:
    """Custom handler for event repository connection errors"""
    return JSONResponse(
        content=exc.detail,
        status_code=exc.status_code
    )


# Domain exception handlers

async def domain_error_handler(
    request: Request,
    exc: DomainError
) -> JSONResponse:
    """Generic handler for all domain errors"""
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
    """Custom handler for event not found from repository"""
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
    """Handler for bet service specific errors"""
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
    """Handler for insufficient balance errors"""
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
    """Handler for invalid bet amount errors"""
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
    Custom handler for response validation errors that often occur when
    coroutines are not properly awaited in API endpoints
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
            message="The server encountered an error while processing the response",
            error_type="ResponseValidationError",
            details={
                "info": "A coroutine was likely not awaited properly in the endpoint handler",
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
    Catch-all handler for any unhandled exceptions
    
    This handler acts as a last resort for exceptions that don't have a specific handler
    """
    # Log the exception here for monitoring and debugging
    error_type = type(exc).__name__
    error_message = str(exc)
    
    # In production, you might want to hide the actual error details from users
    # and just return a generic error message
    return JSONResponse(
        content=ErrorResponse.create(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            error_type="ServerError",
            details={
                "error_type": error_type,
                "error_message": error_message
            }
        ),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers for the application.
    This function should be called during application initialization.
    
    Args:
        app: FastAPI application instance
    """
    # Register legacy exception handlers
    app.add_exception_handler(RemoteServiceUnavailable, remote_service_unavailable_handler)
    app.add_exception_handler(EventByIdNotFound, event_id_not_found_handler)
    app.add_exception_handler(EventRepositoryConnectionError, event_repository_connection_error_handler)
    
    # Register domain exception handlers
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(EventNotFoundError, event_not_found_error_handler)
    app.add_exception_handler(BetServiceError, bet_service_error_handler)
    app.add_exception_handler(InsufficientBalanceError, insufficient_balance_error_handler)
    app.add_exception_handler(InvalidBetAmountError, invalid_bet_amount_error_handler)
    
    # Register validation error handlers
    app.add_exception_handler(ResponseValidationError, response_validation_error_handler)
    
    # Register catch-all handler (always register this last)
    app.add_exception_handler(Exception, catch_all_exception_handler)
