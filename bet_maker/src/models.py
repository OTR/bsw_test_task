import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import declarative_base, sessionmaker, Mapped
from sqlalchemy import Column, DateTime, String, Enum, DECIMAL, ForeignKey, func

from src.config import settings
from src.schemas import BetStatus

Base = declarative_base()


class Bet(Base):
    """ORM модель для ставки"""
    __tablename__ = "bet"

    bet_id: Mapped[str] = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = Column(String, nullable=False)
    amount: Mapped[Decimal] = Column(DECIMAL(10, 2), nullable=False)
    status: Mapped[BetStatus] = Column(Enum(BetStatus), default=BetStatus.PENDING)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
