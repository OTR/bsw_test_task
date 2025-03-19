from datetime import datetime
from decimal import Decimal
from typing import Union, Any, ClassVar, Dict

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.domain.vo import EventStatus


class Event(BaseModel):
    """
    Доменная сущность, представляющая событие для ставок.
    
    Представляет событие из сервиса line-provider в контексте домена bet-maker.
    Содержит всю необходимую информацию о событии, на которое можно сделать ставку.
    
    Attributes:
        event_id: Уникальный идентификатор события
        coefficient: Коэффициент ставки для этого события
        deadline: Unix-время дедлайна для размещения ставок
        status: Текущий статус события
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        json_schema_extra={"example": {
            "event_id": 123,
            "coefficient": "2.50",
            "deadline": 1609459200,
            "status": "NEW"
        }}
    )

    event_id: Union[int, str] = Field(..., description="Уникальный идентификатор события")
    coefficient: Decimal = Field(..., description="Коэффициент ставки с ровно 2 знаками после запятой")
    deadline: int = Field(..., description="Unix-время дедлайна для размещения ставок")
    status: EventStatus = Field(..., description="Текущий статус события")

    @field_validator('coefficient')
    def validate_coefficient(cls, value: Decimal) -> Decimal:
        """
        Проверяет, что коэффициент положительный и имеет ровно 2 знака после запятой.
        
        Args:
            value: Значение коэффициента для проверки
            
        Returns:
            Проверенный коэффициент
            
        Raises:
            ValueError: Если коэффициент не положительный или не имеет ровно 2 знаков после запятой
        """
        if value <= Decimal('0'):
            raise ValueError("Коэффициент должен быть положительным числом")

        decimal_str = str(value)
        if '.' in decimal_str:
            _, decimals = decimal_str.split('.')
            if len(decimals) != 2:
                raise ValueError("Коэффициент должен иметь ровно 2 знака после запятой")

        return value

    @field_validator('status')
    def validate_status(cls, value: Any) -> EventStatus:
        """
        Проверяет и преобразует статус в перечисление EventStatus.
        
        Args:
            value: Значение статуса для проверки (строка или EventStatus)
            
        Returns:
            Проверенное значение перечисления EventStatus
            
        Raises:
            ValueError: Если статус недействителен
        """
        if isinstance(value, EventStatus):
            return value

        return EventStatus.from_string(value)

    @property
    def is_active(self) -> bool:
        """
        Определяет, активно ли событие для ставок.
        Событие активно, если его дедлайн в будущем и статус 'NEW'.
        
        Returns:
            True если событие активно, False в противном случае
        """
        current_time: int = int(datetime.now().timestamp())
        return self.deadline > current_time and self.status.is_active

    @property
    def formatted_deadline(self) -> str:
        """
        Возвращает дедлайн в удобочитаемом формате даты и времени.
        
        Returns:
            Строковое представление временной метки дедлайна
        """
        return datetime.fromtimestamp(self.deadline).strftime("%Y-%m-%d %H:%M:%S")

    def model_dump_json(self, **kwargs) -> str:
        """
        Пользовательский метод сериализации JSON для корректной обработки типов Decimal и enum.
        
        Returns:
            JSON-строка, представляющая модель
        """
        data: Dict[str, Any] = self.model_dump()

        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(value)
            elif isinstance(value, EventStatus):
                data[key] = str(value)

        from json import dumps
        return dumps(data, default=str)
