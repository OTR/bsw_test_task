from decimal import Decimal
from datetime import datetime
from typing import Union, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.domain.vo import BetStatus


class Bet(BaseModel):
    """
    Доменная сущность ставки пользователя.
    
    Attributes:
        bet_id: Уникальный идентификатор ставки
        event_id: ID события, на которое сделана ставка
        amount: Сумма ставки
        status: Текущий статус ставки (в ожидании, выиграна, проиграна)
        created_at: Время создания ставки
    """
    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={"example": {
            "bet_id": 123,
            "event_id": 456,
            "amount": "10.00",
            "status": "PENDING",
            "created_at": "2023-01-01T12:00:00"
        }}
    )
    
    bet_id: Union[int, str] = Field(..., description="Уникальный идентификатор ставки")
    event_id: Union[int, str] = Field(..., description="ID события, на которое сделана ставка")
    amount: Decimal = Field(..., description="Сумма ставки")
    status: BetStatus = Field(default=BetStatus.PENDING, description="Текущий статус ставки")
    created_at: datetime = Field(
        default_factory=datetime.now, 
        description="Время создания ставки"
    )

    @field_validator('amount')
    def validate_amount(cls, value: Decimal) -> Decimal:
        """
        Проверяет сумму ставки на положительность и наличие ровно 2 знаков после запятой.
        
        Args:
            value: Сумма ставки для проверки
            
        Returns:
            Проверенная сумма ставки
            
        Raises:
            ValueError: Если сумма не положительная или имеет не ровно 2 знака после запятой
        """
        if value <= Decimal('0'):
            raise ValueError("Сумма ставки должна быть положительной")
            
        decimal_str = str(value)
        if '.' in decimal_str:
            _, decimals = decimal_str.split('.')
            if len(decimals) != 2:
                raise ValueError("Сумма ставки должна иметь ровно 2 знака после запятой")
                
        return value

    @field_validator('status')
    def validate_status(cls, value: Any) -> BetStatus:
        """
        Проверяет и преобразует статус в перечисление BetStatus.
        
        Args:
            value: Значение статуса (строка или BetStatus)
            
        Returns:
            Проверенное значение перечисления BetStatus
            
        Raises:
            ValueError: Если статус недействителен
        """
        if isinstance(value, BetStatus):
            return value
            
        try:
            return BetStatus(value)
        except ValueError:
            raise ValueError(f"Недействительный статус ставки: {value}")

    @property
    def is_settled(self) -> bool:
        """
        Определяет, разрешена ли ставка (выиграна или проиграна).
        
        Returns:
            True если ставка разрешена, False если еще в ожидании
        """
        return self.status != BetStatus.PENDING
    
    @property
    def is_winning(self) -> bool:
        """
        Определяет, является ли ставка выигрышной.
        
        Returns:
            True если ставка выиграла, False в противном случае
        """
        return self.status == BetStatus.WON
    
    @property
    def formatted_amount(self) -> str:
        """
        Возвращает сумму ставки в форматированном виде с символом валюты.
        
        Returns:
            Форматированная строка с суммой ставки
        """
        return f"${self.amount}"
    
    def update_status_from_event_state(self, event_state: str) -> 'Bet':
        """
        Создает новый экземпляр Bet с обновленным статусом на основе состояния события.

        Args:
            event_state: Состояние события от сервиса line_provider

        Returns:
            Новый экземпляр Bet с обновленным статусом
        """
        new_status = BetStatus.from_event_state(event_state)
        return self.model_copy(update={"status": new_status})

    def model_dump_json(self, **kwargs) -> str:
        """
        Кастомный метод сериализации в JSON для корректной обработки Decimal и перечислений.

        Returns:
            JSON-строка модели
        """
        data = self.model_dump()

        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(value)
            elif isinstance(value, BetStatus):
                data[key] = str(value)

        from json import dumps
        return dumps(data, default=str)


class BetRequest(BaseModel):
    """
    DTO для создания новой ставки.

    Attributes:
        event_id: ID события для ставки
        amount: Сумма ставки
    """
    model_config = ConfigDict(
        frozen=True,
        extra="forbid"
    )

    event_id: int = Field(..., description="ID события для ставки")
    amount: Decimal = Field(..., description="Сумма ставки")

    @field_validator('amount')
    def validate_amount(cls, value: Decimal) -> Decimal:
        """
        Проверяет сумму ставки на положительность и наличие ровно 2 знаков после запятой.

        Args:
            value: Сумма ставки для проверки

        Returns:
            Проверенная сумма ставки

        Raises:
            ValueError: Если сумма не положительная или имеет не ровно 2 знака после запятой
        """
        if value <= Decimal('0'):
            raise ValueError("Сумма ставки должна быть положительной")

        decimal_str = str(value)
        if '.' in decimal_str:
            _, decimals = decimal_str.split('.')
            if len(decimals) != 2:
                raise ValueError("Сумма ставки должна иметь ровно 2 знака после запятой")

        return value


class BetResponse(BaseModel):
    """
    DTO для информации о ставке в ответах API.

    Attributes:
        bet_id: Уникальный идентификатор ставки
        event_id: ID события, на которое сделана ставка
        amount: Сумма ставки
        status: Текущий статус ставки
        created_at: Время создания ставки
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {
            "bet_id": 123,
            "event_id": 456,
            "amount": "10.00",
            "status": "PENDING",
            "created_at": "2023-01-01T12:00:00"
        }}
    )

    bet_id: int = Field(..., description="Уникальный идентификатор ставки")
    event_id: int = Field(..., description="ID события, на которое сделана ставка")
    amount: Decimal = Field(..., description="Сумма ставки")
    status: BetStatus = Field(..., description="Текущий статус ставки")
    created_at: datetime = Field(..., description="Время создания ставки")
