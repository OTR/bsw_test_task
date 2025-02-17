class LineProviderError(Exception):
    """Base class for all Line Provider errors"""


class EventNotFoundError(LineProviderError):
    """Raised when an event is not found in the repository"""
    def __init__(self, event_id: int):
        super().__init__(f"Event by `event_id` = {event_id} not found")
        self.event_id: int = event_id


class EventAlreadyExistsError(LineProviderError):
    """Raised when attempting to create an event that already exists"""
    def __init__(self, event_id: int):
        super().__init__(f"Event with `event_id` = {event_id} already exists")
        self.event_id: int = event_id


class InvalidEventDeadlineError(LineProviderError):
    """
    Raised when event deadline is invalid.
    
    This can happen for two reasons:
    1. The deadline is not a positive number (≤ 0)
    2. The deadline is not in the future (≤ current_time)
    """
    def __init__(self, deadline: int, current_time: int):
        if deadline <= 0:
            message = f"Event deadline ({deadline}) is invalid. Must be a positive Unix timestamp."
        else:
            message = f"Event deadline ({deadline}) must be in the future. Current time: {current_time}"
        
        self.deadline = deadline
        self.current_time = current_time
        super().__init__(message)
