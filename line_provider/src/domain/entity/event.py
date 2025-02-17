from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, condecimal, model_validator, field_validator

from src.domain.vo.event_status import EventStatus
from src.exception.exceptions import InvalidEventDeadlineError


class Event(BaseModel):
    """
    Representing betting Event
    
    Attributes:
        event_id: Unique identifier for the event (positive integer)
        coefficient: Betting coefficient (strictly positive number with 2 decimal places)
        deadline: Timestamp until which bets are accepted
        status: Current event status (NEW, FINISHED_WIN, FINISHED_LOSE)
    """
    event_id: int = Field(ge=0, description="Unique event identifier")
    coefficient: condecimal(gt=0, decimal_places=2) = Field(description="Betting coefficient")  # type: ignore
    deadline: int = Field(gt=0, description="Timestamp until which bets are accepted")
    status: EventStatus = Field(default=EventStatus.NEW, description="Current event status")

    @model_validator(mode='after')
    def validate_event(self) -> 'Event':
        """
        Validate event data, specifically:
        1. Ensure deadline is a positive number
        2. Ensure deadline is in the future
        
        Raises:
            InvalidEventDeadlineError: When deadline validation fails
        """
        current_time: int = int(datetime.now().timestamp())
        
        # Check if deadline is a positive number - this should be caught by Field(gt=0)
        # but we include it here as a safety check
        if self.deadline <= 0:
            raise InvalidEventDeadlineError(
                deadline=self.deadline,
                current_time=current_time,
            )
            
        # Check if deadline is in the future
        if self.deadline <= current_time:
            raise InvalidEventDeadlineError(
                deadline=self.deadline,
                current_time=current_time,
            )
            
        return self

    @property
    def is_finished(self) -> bool:
        """Check if Event status is finished"""
        return self.status in (EventStatus.FINISHED_WIN, EventStatus.FINISHED_LOSE)

    @property
    def is_active(self) -> bool:
        """Check if event is active (not finished and deadline not passed)"""
        current_time = int(datetime.now().timestamp())
        return not self.is_finished and self.deadline > current_time


class CreateEventRequest(BaseModel):
    """DTO for event creation request."""
    event_id: int = Field(ge=0, description="Unique event identifier")
    coefficient: condecimal(gt=0, decimal_places=2) = Field(description="Betting coefficient")  # type: ignore
    deadline: int = Field(gt=0, description="Timestamp until which bets are accepted")
    status: EventStatus = Field(default=EventStatus.NEW, description="Current event status")

    @field_validator('coefficient')
    @classmethod
    def validate_coefficient_decimal_places(cls, v: Decimal) -> Decimal:
        """
        Validate that coefficient has exactly 2 decimal places.
        
        Args:
            v: Coefficient value
            
        Returns:
            Original value if valid
            
        Raises:
            ValueError: If coefficient doesn't have exactly 2 decimal places
        """
        # Convert to string and split by decimal point
        str_value = str(v)
        if '.' in str_value:
            decimal_places = len(str_value.split('.')[1])
            if decimal_places != 2:
                raise ValueError(f"Coefficient must have exactly 2 decimal places, got {decimal_places}")
        else:
            raise ValueError("Coefficient must have exactly 2 decimal places, got 0")
        
        return v

    def to_domain(self) -> Event:
        """
        Convert DTO to domain model.
        
        This conversion triggers domain validation rules in the Event class,
        including deadline validation.
        
        Returns:
            Event: Domain entity with validated data
            
        Raises:
            InvalidEventDeadlineError: When deadline validation fails
        """
        return Event(
            event_id=self.event_id,
            coefficient=self.coefficient,
            deadline=self.deadline,
            status=self.status
        )


class CreateEventResponse(BaseModel):
    """Response for event creation."""
    success: bool = Field(description="Whether the operation was successful")
    event_id: int = Field(description="ID of the created/updated event")


class EventResponse(BaseModel):
    """DTO for event response."""
    event_id: int = Field(description="Unique event identifier")
    coefficient: Decimal = Field(description="Betting coefficient")
    deadline: int = Field(description="Timestamp until which bets are accepted")
    status: EventStatus = Field(description="Current event status")
    is_active: bool = Field(description="Whether the event is active")

    @classmethod
    def from_domain(cls, event: Event) -> 'EventResponse':
        """Convert domain model to DTO."""
        return cls(
            event_id=event.event_id,
            coefficient=event.coefficient,
            deadline=event.deadline,
            status=event.status,
            is_active=event.is_active
        )
