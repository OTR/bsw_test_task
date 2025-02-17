from datetime import datetime
from decimal import Decimal
from typing import Union, Any, ClassVar, Dict

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.domain.vo import EventStatus


class Event(BaseModel):
    """
    Domain entity representing a betting event.
    
    This entity is a representation of an event from the line-provider service
    within the bet-maker domain context. It contains all relevant information
    about an event that can be bet on.
    
    Attributes:
        event_id: Unique identifier of the event
        coefficient: The betting coefficient (odds) for this event
        deadline: Unix timestamp indicating the deadline for placing bets
        status: Current status of the event
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,  # Make the entity immutable
        json_schema_extra={"example": {
            "event_id": 123,
            "coefficient": "2.50",
            "deadline": 1609459200,
            "status": "NEW"
        }}
    )
    
    event_id: Union[int, str] = Field(..., description="Unique identifier of the event")
    coefficient: Decimal = Field(..., description="Betting coefficient with exactly 2 decimal places")
    deadline: int = Field(..., description="Unix timestamp deadline for placing bets")
    status: EventStatus = Field(..., description="Current status of the event")

    @field_validator('coefficient')
    def validate_coefficient(cls, value: Decimal) -> Decimal:
        """
        Validates that the coefficient is a positive number with exactly 2 decimal places.
        
        Args:
            value: The coefficient value to validate
            
        Returns:
            The validated coefficient
            
        Raises:
            ValueError: If coefficient is not positive or doesn't have exactly 2 decimal places
        """
        # Check if coefficient is positive
        if value <= Decimal('0'):
            raise ValueError("Coefficient must be a positive number")
            
        # Check if coefficient has exactly 2 decimal places
        decimal_str: str = str(value)
        if '.' in decimal_str:
            _, decimals = decimal_str.split('.')
            if len(decimals) != 2:
                raise ValueError("Coefficient must have exactly 2 decimal places")
                
        return value

    @field_validator('status')
    def validate_status(cls, value: Any) -> EventStatus:
        """
        Validates and converts the status to an EventStatus enum.
        
        Args:
            value: The status value to validate (string or EventStatus)
            
        Returns:
            The validated EventStatus enum value
            
        Raises:
            ValueError: If the status is not valid
        """
        if isinstance(value, EventStatus):
            return value
            
        return EventStatus.from_string(value)

    @property
    def is_active(self) -> bool:
        """
        Determines if the event is still active for betting.
        An event is active if its deadline is in the future and its status is 'NEW'.
        
        Returns:
            True if the event is active, False otherwise
        """
        current_time: int = int(datetime.now().timestamp())
        return self.deadline > current_time and self.status.is_active
    
    @property
    def formatted_deadline(self) -> str:
        """
        Returns the deadline formatted as a human-readable date and time string.
        
        Returns:
            A string representation of the deadline timestamp
        """
        return datetime.fromtimestamp(self.deadline).strftime("%Y-%m-%d %H:%M:%S")
    
    def model_dump_json(self, **kwargs) -> str:
        """
        Custom JSON serialization method to properly handle Decimal and enum types.
        
        Returns:
            JSON string representation of the model
        """
        # First convert the model to a dict
        data: Dict[str, Any] = self.model_dump()
        
        # Manually convert Decimal and Enum values to strings
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(value)
            elif isinstance(value, EventStatus):
                data[key] = str(value)
        
        # Use json.dumps with custom handling for serialization
        from json import dumps
        return dumps(data, default=str)
