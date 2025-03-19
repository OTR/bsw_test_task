from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, condecimal, model_validator, field_validator

from src.domain.vo import EventStatus
from src.exception.exceptions import InvalidEventDeadlineError


class Event(BaseModel):
    """
    Модель события для ставок
    
    Attributes:
        event_id: Уникальный идентификатор события (положительное целое число)
        coefficient: Коэффициент ставки (положительное число с 2 знаками после запятой)
        deadline: Время, до которого принимаются ставки
        status: Текущий статус события (NEW, FINISHED_WIN, FINISHED_LOSE)
    """
    event_id: int = Field(ge=0, description="Уникальный идентификатор события")
    coefficient: condecimal(gt=0, decimal_places=2) = Field(description="Коэффициент ставки")  # type: ignore
    deadline: int = Field(gt=0, description="Время, до которого принимаются ставки")
    status: EventStatus = Field(default=EventStatus.NEW, description="Текущий статус события")

    @model_validator(mode='after')
    def validate_event(self) -> 'Event':
        """
        Проверка данных события:
        1. Срок должен быть положительным числом
        2. Срок должен быть в будущем
        
        Raises:
            InvalidEventDeadlineError: При неверном сроке события
        """
        current_time: int = int(datetime.now().timestamp())

        if self.deadline <= 0:
            raise InvalidEventDeadlineError(
                deadline=self.deadline,
                current_time=current_time,
            )

        if self.deadline <= current_time:
            raise InvalidEventDeadlineError(
                deadline=self.deadline,
                current_time=current_time,
            )

        return self

    @property
    def is_finished(self) -> bool:
        """Проверка, завершено ли событие"""
        return self.status in (EventStatus.FINISHED_WIN, EventStatus.FINISHED_LOSE)

    @property
    def is_active(self) -> bool:
        """Проверка, активно ли событие (не завершено и срок не истек)"""
        current_time = int(datetime.now().timestamp())
        return not self.is_finished and self.deadline > current_time


class CreateEventRequest(BaseModel):
    """Запрос на создание события."""
    event_id: int = Field(ge=0, description="Уникальный идентификатор события")
    coefficient: condecimal(gt=0, decimal_places=2) = Field(description="Коэффициент ставки")  # type: ignore
    deadline: int = Field(gt=0, description="Время, до которого принимаются ставки")
    status: EventStatus = Field(default=EventStatus.NEW, description="Текущий статус события")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": 1,
                "coefficient": "1.50",
                "deadline": 1742709198,
                "status": "NEW"
            }
        }
    }

    @field_validator('coefficient')
    @classmethod
    def validate_coefficient_decimal_places(cls, v: Decimal) -> Decimal:
        """
        Проверка, что коэффициент имеет ровно 2 знака после запятой.
        
        Args:
            v: Значение коэффициента
            
        Returns:
            Исходное значение, если оно верно
            
        Raises:
            ValueError: Если коэффициент не имеет ровно 2 знаков после запятой
        """
        str_value = str(v)
        if '.' in str_value:
            decimal_places = len(str_value.split('.')[1])
            if decimal_places != 2:
                raise ValueError(f"Коэффициент должен иметь ровно 2 знака после запятой, получено {decimal_places}")
        else:
            raise ValueError("Коэффициент должен иметь ровно 2 знака после запятой, получено 0")

        return v

    def to_domain(self) -> Event:
        """
        Преобразование DTO в доменную модель.
        
        Это преобразование запускает правила валидации в классе Event,
        включая проверку срока.
        
        Returns:
            Event: Доменная сущность с проверенными данными
            
        Raises:
            InvalidEventDeadlineError: При неверном сроке события
        """
        return Event(
            event_id=self.event_id,
            coefficient=self.coefficient,
            deadline=self.deadline,
            status=self.status
        )


class CreateEventResponse(BaseModel):
    """Ответ на создание события."""
    success: bool = Field(description="Успешность операции")
    event_id: int = Field(description="ID созданного/обновленного события")


class EventResponse(BaseModel):
    """Ответ с данными события."""
    event_id: int = Field(description="Уникальный идентификатор события")
    coefficient: Decimal = Field(description="Коэффициент ставки")
    deadline: int = Field(description="Время, до которого принимаются ставки")
    status: EventStatus = Field(description="Текущий статус события")
    is_active: bool = Field(description="Активно ли событие")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": 1,
                "coefficient": "1.50",
                "deadline": 1742709198,
                "status": "NEW",
                "is_active": True
            }
        }
    }

    @classmethod
    def from_domain(cls, event: Event) -> 'EventResponse':
        """Преобразование доменной модели в DTO."""
        return cls(
            event_id=event.event_id,
            coefficient=event.coefficient,
            deadline=event.deadline,
            status=event.status,
            is_active=event.is_active
        )
