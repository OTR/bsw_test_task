from enum import Enum
from typing import Self


class BetStatus(str, Enum):
    """
    Статус ставки
    
    Values:
        PENDING - Ставка сделана, но результат еще не определен
        WON - Ставка выиграла
        LOST - Ставка проиграла
    """
    PENDING: str = "PENDING"
    WON: str = "WON"
    LOST: str = "LOST"
    
    @classmethod
    def from_event_state(cls, event_state: str) -> Self:
        """
        Преобразует статус события в статус ставки
        
        Args:
            event_state: Статус события из сервиса line_provider
                         (NEW, FINISHED_WIN, FINISHED_LOSE)
        
        Returns:
            Соответствующий статус ставки
        """
        event_status_mapping = {
            "FINISHED_WIN": cls.WON,
            "FINISHED_LOSE": cls.LOST
        }
        
        return event_status_mapping.get(event_state, cls.PENDING)
    
    def __str__(self) -> str:
        return self.value
