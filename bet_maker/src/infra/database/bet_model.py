from decimal import Decimal
from datetime import datetime

from sqlalchemy import Integer, func, text
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.types import Enum

from src.domain.vo import BetStatus
from src.infra.database.base_model import Base


class BetModel(Base):
    """
    ORM модель для сущности ставки. Представляет ставку, сделанную пользователем на событие в базе данных.

    Fields:
        bet_id: Уникальный идентификатор ставки
        event_id: ID события, на которое сделана ставка
        amount: Денежная сумма ставки (с 2 знаками после запятой)
        status: Текущий статус ставки (PENDING, WON, LOST)
        created_at: Время создания ставки
    """
    bet_id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="Уникальный идентификатор ставки"
    )
    
    event_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        index=True,
        comment="ID события, на которое сделана ставка"
    )
    
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        comment="Денежная сумма ставки (с 2 знаками после запятой)"
    )
    
    status: Mapped[BetStatus] = mapped_column(
        Enum(BetStatus),
        default=BetStatus.PENDING,
        nullable=False,
        comment="Текущий статус ставки (PENDING, WON, LOST)"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        comment="Время (timestamp) создания ставки"
    )
    
    def __repr__(self) -> str:
        return f"Bet(id={self.bet_id}, event_id={self.event_id}, amount={self.amount}, status={self.status})"
