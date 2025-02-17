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
    ORM model for bet entity.
    
    Represents a bet placed by a user on an event in the database.
    Fields:
        bet_id: Unique identifier for the bet
        event_id: ID of the event this bet is placed on
        amount: Monetary amount of the bet (with 2 decimal places)
        status: Current status of the bet (PENDING, WON, LOST)
        created_at: Timestamp when the bet was created
    """
    bet_id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="Unique identifier for the bet"
    )
    
    event_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        index=True,
        comment="ID of the event this bet is placed on"
    )
    
    # Amount with exactly 2 decimal places
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        comment="Monetary amount of the bet (with 2 decimal places)"
    )
    
    status: Mapped[BetStatus] = mapped_column(
        Enum(BetStatus),
        default=BetStatus.PENDING,
        nullable=False,
        comment="Current status of the bet (PENDING, WON, LOST)"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        comment="Timestamp when the bet was created"
    )
    
    def __repr__(self) -> str:
        """String representation of the bet model."""
        return f"Bet(id={self.bet_id}, event_id={self.event_id}, amount={self.amount}, status={self.status})"
