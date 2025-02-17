from enum import Enum
from typing import Self


class BetStatus(str, Enum):
    """
    Value object representing the status of a bet
    
    Values:
        PENDING - Bet is placed but the outcome is not yet determined
        WON - Bet has won (the corresponding event finished with a win)
        LOST - Bet has lost (the corresponding event finished with a loss)
    """
    PENDING: str = "PENDING"
    WON: str = "WON"
    LOST: str = "LOST"
    
    @classmethod
    def from_event_state(cls, event_state: str) -> Self:
        """
        Maps an event state to a bet status
        
        Args:
            event_state: The state of the event from line_provider service
                         (NEW, FINISHED_WIN, FINISHED_LOSE)
        
        Returns:
            The corresponding BetStatus
        """
        event_status_mapping = {
            "FINISHED_WIN": cls.WON,
            "FINISHED_LOSE": cls.LOST
        }
        
        return event_status_mapping.get(event_state, cls.PENDING)
    
    def __str__(self) -> str:
        """
        String representation of the bet status
        
        Returns:
            String value of the enum
        """
        return self.value
