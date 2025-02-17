from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, condecimal


class EventStatus(Enum):
    """Статус события"""
    NEW = "NEW"
    FINISHED_WIN = "FINISHED_WIN"
    FINISHED_LOSE = "FINISED_LOSE"


class Event(BaseModel):
    """Событие"""
    event_id: str
    coefficient: Optional[condecimal(gt=0, decimal_places=2)] = Field(default=None)  # type: ignore
    deadline: Optional[int] = None
    status: Optional[EventStatus] = None

    @property
    def is_finished(self) -> bool:
        """Завершено ли событие"""
        return self.state in (EventStatus.FINISHED_WIN, EventStatus.FINISHED_LOSE)
