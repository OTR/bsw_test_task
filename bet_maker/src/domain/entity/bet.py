from decimal import Decimal
from datetime import datetime
from typing import  Union, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.domain.vo import BetStatus


class Bet(BaseModel):
    """
    Domain entity representing a bet placed by a user.
    
    This entity encapsulates all the information related to a bet including its
    amount, associated event, status, and creation timestamp.
    
    Attributes:
        bet_id: Unique identifier of the bet
        event_id: ID of the event this bet is placed on
        amount: The monetary amount of the bet
        status: Current status of the bet (pending, won, lost)
        created_at: Timestamp when the bet was created
    """
    model_config = ConfigDict(
        frozen=True,  # Make the entity immutable
        json_schema_extra={"example": {
            "bet_id": 123,
            "event_id": 456,
            "amount": "10.00",
            "status": "PENDING",
            "created_at": "2023-01-01T12:00:00"
        }}
    )
    
    bet_id: Union[int, str] = Field(..., description="Unique identifier of the bet")
    event_id: Union[int, str] = Field(..., description="ID of the event this bet is placed on")
    amount: Decimal = Field(..., description="Monetary amount of the bet")
    status: BetStatus = Field(default=BetStatus.PENDING, description="Current status of the bet")
    created_at: datetime = Field(
        default_factory=datetime.now, 
        description="Timestamp when the bet was created"
    )

    @field_validator('amount')
    def validate_amount(cls, value: Decimal) -> Decimal:
        """
        Validates that the bet amount is a positive number with exactly 2 decimal places.
        
        Args:
            value: The bet amount to validate
            
        Returns:
            The validated bet amount
            
        Raises:
            ValueError: If amount is not positive or doesn't have exactly 2 decimal places
        """
        # Check if amount is positive
        if value <= Decimal('0'):
            raise ValueError("Bet amount must be a positive number")
            
        # Check if amount has exactly 2 decimal places
        decimal_str = str(value)
        if '.' in decimal_str:
            _, decimals = decimal_str.split('.')
            if len(decimals) != 2:
                raise ValueError("Bet amount must have exactly 2 decimal places")
                
        return value

    @field_validator('status')
    def validate_status(cls, value: Any) -> BetStatus:
        """
        Validates and converts the status to a BetStatus enum.
        
        Args:
            value: The status value to validate (string or BetStatus)
            
        Returns:
            The validated BetStatus enum value
            
        Raises:
            ValueError: If the status is not valid
        """
        if isinstance(value, BetStatus):
            return value
            
        try:
            return BetStatus(value)
        except ValueError:
            raise ValueError(f"Invalid bet status: {value}")

    @property
    def is_settled(self) -> bool:
        """
        Determines if the bet has been settled (won or lost).
        
        Returns:
            True if the bet is settled, False if it's still pending
        """
        return self.status != BetStatus.PENDING
    
    @property
    def is_winning(self) -> bool:
        """
        Determines if this is a winning bet.
        
        Returns:
            True if the bet has won, False otherwise
        """
        return self.status == BetStatus.WON
    
    @property
    def formatted_amount(self) -> str:
        """
        Returns the bet amount formatted as a string with currency symbol.
        
        Returns:
            A formatted string representation of the bet amount
        """
        return f"${self.amount}"
    
    def update_status_from_event_state(self, event_state: str) -> 'Bet':
        """
        Creates a new Bet instance with updated status based on event state.
        Since Bet is immutable, this method returns a new instance.
        
        Args:
            event_state: The state of the event from line_provider service
            
        Returns:
            A new Bet instance with the updated status
        """
        new_status = BetStatus.from_event_state(event_state)
        return self.model_copy(update={"status": new_status})
    
    def model_dump_json(self, **kwargs) -> str:
        """
        Custom JSON serialization method to properly handle Decimal and enum types.
        
        Returns:
            JSON string representation of the model
        """
        # First convert the model to a dict
        data = self.model_dump()
        
        # Manually convert Decimal and Enum values to strings
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(value)
            elif isinstance(value, BetStatus):
                data[key] = str(value)
        
        # Use the standard model_dump_json with the preprocessed data
        from json import dumps
        return dumps(data, default=str)


class BetRequest(BaseModel):
    """
    Data Transfer Object (DTO) for creating a new bet.
    
    This class represents the incoming data structure for bet creation requests.
    It contains only the essential fields needed to create a bet.
    
    Attributes:
        event_id: ID of the event to bet on
        amount: The monetary amount of the bet
    """
    model_config = ConfigDict(
        frozen=True,
        extra="forbid"  # Prevent extra fields
    )
    
    event_id: int = Field(..., description="ID of the event to bet on")
    amount: Decimal = Field(..., description="Monetary amount to bet")
    
    @field_validator('amount')
    def validate_amount(cls, value: Decimal) -> Decimal:
        """
        Validates that the bet amount is a positive number with exactly 2 decimal places.
        
        Args:
            value: The bet amount to validate
            
        Returns:
            The validated bet amount
            
        Raises:
            ValueError: If amount is not positive or doesn't have exactly 2 decimal places
        """
        # Check if amount is positive
        if value <= Decimal('0'):
            raise ValueError("Bet amount must be a positive number")
            
        # Check if amount has exactly 2 decimal places
        decimal_str = str(value)
        if '.' in decimal_str:
            _, decimals = decimal_str.split('.')
            if len(decimals) != 2:
                raise ValueError("Bet amount must have exactly 2 decimal places")
                
        return value


class BetResponse(BaseModel):
    """
    Data Transfer Object (DTO) for bet information in responses.
    
    This class represents the outgoing data structure for bet information
    in API responses. It includes all relevant bet data for client consumption.
    
    Attributes:
        bet_id: Unique identifier of the bet
        event_id: ID of the event this bet is placed on
        amount: The monetary amount of the bet
        status: Current status of the bet
        created_at: Timestamp when the bet was created
    """
    model_config = ConfigDict(
        from_attributes=True,  # Allow creation from ORM objects
        json_schema_extra={"example": {
            "bet_id": 123,
            "event_id": 456,
            "amount": "10.00",
            "status": "PENDING",
            "created_at": "2023-01-01T12:00:00"
        }}
    )
    
    bet_id: int = Field(..., description="Unique identifier of the bet")
    event_id: int = Field(..., description="ID of the event this bet is placed on")
    amount: Decimal = Field(..., description="Monetary amount of the bet")
    status: BetStatus = Field(..., description="Current status of the bet")
    created_at: datetime = Field(..., description="Timestamp when the bet was created")
