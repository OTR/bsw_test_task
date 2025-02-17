from enum import Enum
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BetStatus(Enum):
    """Статус ставки"""
    PENDING = "PENDING"
    WON = "WON"
    LOST = "LOST"

    @staticmethod
    def from_event_state(event_state: str) -> "BetStatus":
        """Отобразить статус события в статус ставки"""
        if event_state == "FINISHED_WIN":
            return BetStatus.WON
        elif event_state == "FINISHED_LOSE":
            return BetStatus.LOST

        return BetStatus.PENDING


class BetRequest(BaseModel):
    """Входной DTO на создание ставки"""
    event_id: str
    amount: Decimal


class BetResponse(BaseModel):
    """Выходной DTO для истории ставок"""
    model_config = ConfigDict(from_attributes=True)
    bet_id: str
    event_id: int
    amount: Decimal
    status: BetStatus
    created_at: datetime
