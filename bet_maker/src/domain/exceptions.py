"""
Domain exceptions module.

This module contains custom exceptions for the domain layer.
These exceptions represent domain-specific error conditions.
"""
from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base exception for all domain errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EventNotFoundError(DomainError):
    """Exception raised when an event is not found."""
    
    def __init__(self, event_id: Any):
        super().__init__(f"Event with ID {event_id} not found")


class BetServiceError(DomainError):
    """Exception raised when there's an error in the bet service."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        super().__init__(message)


class InsufficientBalanceError(BetServiceError):
    """Exception raised when the user has insufficient balance for a bet."""
    
    def __init__(self, user_id: Any, amount_required: float, amount_available: float):
        self.user_id = user_id
        self.amount_required = amount_required
        self.amount_available = amount_available
        super().__init__(
            f"Insufficient balance for user {user_id}. Required: {amount_required}, Available: {amount_available}",
            {
                "user_id": user_id,
                "amount_required": amount_required,
                "amount_available": amount_available,
            },
        )


class InvalidBetAmountError(BetServiceError):
    """Exception raised when the bet amount is invalid."""
    
    def __init__(self, amount: float, min_amount: float, max_amount: float):
        self.amount = amount
        self.min_amount = min_amount
        self.max_amount = max_amount
        super().__init__(
            f"Invalid bet amount: {amount}. Must be between {min_amount} and {max_amount}",
            {
                "amount": amount,
                "min_amount": min_amount,
                "max_amount": max_amount,
            },
        )
