from typing import Any, Dict, Optional


class DomainError(Exception):
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EventNotFoundError(DomainError):
    
    def __init__(self, event_id: Any):
        super().__init__(f"Событие с ID {event_id} не найдено")


class BetServiceError(DomainError):
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        super().__init__(message)


class InsufficientBalanceError(BetServiceError):
    
    def __init__(self, user_id: Any, amount_required: float, amount_available: float):
        self.user_id = user_id
        self.amount_required = amount_required
        self.amount_available = amount_available
        super().__init__(
            f"Недостаточно средств у пользователя {user_id}. Требуется: {amount_required}, Доступно: {amount_available}",
            {
                "user_id": user_id,
                "amount_required": amount_required,
                "amount_available": amount_available,
            },
        )


class InvalidBetAmountError(BetServiceError):
    
    def __init__(self, amount: float, min_amount: float, max_amount: float):
        self.amount = amount
        self.min_amount = min_amount
        self.max_amount = max_amount
        super().__init__(
            f"Недопустимая сумма ставки: {amount}. Должна быть между {min_amount} и {max_amount}",
            {
                "amount": amount,
                "min_amount": min_amount,
                "max_amount": max_amount,
            },
        )
