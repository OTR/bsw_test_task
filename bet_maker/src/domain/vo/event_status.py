from enum import Enum
from typing import Self


class EventStatus(str, Enum):
    """
    Value object representing the status of an event
    
    This is a mirror of the event status from the line-provider service,
    but defined in the bet-maker domain for proper encapsulation.
    
    Values:
        NEW - Event is active and bets can be placed
        FINISHED_WIN - Event finished with a win (first team won)
        FINISHED_LOSE - Event finished with a loss (first team lost)
    """
    NEW: str = "NEW"
    FINISHED_WIN: str = "FINISHED_WIN"
    FINISHED_LOSE: str = "FINISHED_LOSE"
    
    @classmethod
    def from_string(cls, status_str: str) -> Self:
        """
        Creates an EventStatus from a string value
        
        Args:
            status_str: String representation of the status
        
        Returns:
            The corresponding EventStatus enum value
            
        Raises:
            ValueError: If the status string is not valid
        """
        try:
            return cls(status_str)
        except ValueError:
            valid_values = [e.value for e in cls]
            raise ValueError(f"Invalid event status: {status_str}. Valid values are: {', '.join(valid_values)}")
    
    @property
    def is_active(self) -> bool:
        """
        Determines if the event is still active for betting
        
        Returns:
            True if the event is active (NEW), False otherwise
        """
        return self == self.NEW
    
    @property
    def is_finished(self) -> bool:
        """
        Determines if the event is finished
        
        Returns:
            True if the event is finished (FINISHED_WIN or FINISHED_LOSE), False otherwise
        """
        return self in (self.FINISHED_WIN, self.FINISHED_LOSE)
    
    def __str__(self) -> str:
        """
        String representation of the event status
        
        Returns:
            String value of the enum
        """
        return self.value
