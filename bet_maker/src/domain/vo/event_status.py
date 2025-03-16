from enum import Enum
from typing import Self


class EventStatus(str, Enum):
    """
    Статус события
    
    Values:
        NEW - Событие активно, можно делать ставки
        FINISHED_WIN - Событие завершилось победой
        FINISHED_LOSE - Событие завершилось поражением
    """
    NEW: str = "NEW"
    FINISHED_WIN: str = "FINISHED_WIN"
    FINISHED_LOSE: str = "FINISHED_LOSE"
    
    @classmethod
    def from_string(cls, status_str: str) -> Self:
        """
        Создает статус события из строки
        
        Args:
            status_str: Строковое представление статуса
        
        Returns:
            Соответствующий статус события
            
        Raises:
            ValueError: Если строка статуса недопустима
        """
        try:
            return cls(status_str)
        except ValueError:
            valid_values = [e.value for e in cls]
            raise ValueError(f"Недопустимый статус события: {status_str}. Допустимые значения: {', '.join(valid_values)}")
    
    @property
    def is_active(self) -> bool:
        """
        Проверяет, активно ли событие для ставок
        
        Returns:
            True если событие активно (NEW), False в противном случае
        """
        return self == self.NEW
    
    @property
    def is_finished(self) -> bool:
        """
        Проверяет, завершено ли событие
        
        Returns:
            True если событие завершено (FINISHED_WIN или FINISHED_LOSE), False в противном случае
        """
        return self in (self.FINISHED_WIN, self.FINISHED_LOSE)
    
    def __str__(self) -> str:
        return self.value
