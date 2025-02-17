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
    Create a standardized error response dictionary.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_type: Type of error (class name)
        
    Returns:
        Dictionary with error details
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
    Handle Pydantic validation errors.
    This handler will catch domain exceptions raised during validation.
    """
    # Extract the original error if it's wrapped in ValidationError
    if exc.raw_errors:
        for error in exc.raw_errors:
            if hasattr(error, 'exc'):
                original_error = error.exc
                if isinstance(original_error, LineProviderError):
                    # Route to the appropriate domain exception handler
                    if isinstance(original_error, InvalidEventDeadlineError):
                        return await invalid_event_deadline_handler(request, original_error)
                    if isinstance(original_error, EventNotFoundError):
                        return await event_not_found_handler(request, original_error)
                    if isinstance(original_error, EventAlreadyExistsError):
                        return await event_already_exists_handler(request, original_error)
                    return await line_provider_error_handler(request, original_error)
            elif isinstance(error, InvalidEventDeadlineError):
                return await invalid_event_deadline_handler(request, error)
    
    # Handle regular validation errors
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
    Handle FastAPI request validation errors.
    
    This catches validation errors from the API layer before they reach
    the domain models. For deadline validation that happens in the domain
    models, see validation_error_handler.
    """
    # Check if this contains an embedded InvalidEventDeadlineError
    # This can happen if the request validation triggers a domain validation
    if hasattr(exc, 'raw_errors'):
        for error in exc.raw_errors:
            if hasattr(error, 'exc') and isinstance(error.exc, LineProviderError):
                original_error = error.exc
                # Route to appropriate domain exception handler
                if isinstance(original_error, InvalidEventDeadlineError):
                    return await invalid_event_deadline_handler(request, original_error)
                # Other domain exceptions can be handled similarly

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,  # Use 400 instead of 422 for API validation errors
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
    """Handle EventNotFoundError exceptions."""
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
    """Handle EventAlreadyExistsError exceptions."""
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
    Handle InvalidEventDeadlineError exceptions.
    
    This handles validation errors related to event deadlines,
    which can be either negative/zero or not in the future.
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
    Handle any unhandled LineProviderError exceptions.
    This is a catch-all handler for domain exceptions that don't have specific handlers.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(exc),
            error_type=exc.__class__.__name__
        )
    )


# Map of exception types to their handlers
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
    Register all error handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    for exception_class, handler in exception_handlers.items():
        app.add_exception_handler(exception_class, handler)
