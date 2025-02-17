from decimal import Decimal

import pytest
from pydantic import ValidationError

from ..src.schemas import Event

def test_valid_event_creation():
    """
    Проверяем создание валидных событий с разными коэффициентами
    1.5 Должно автоматически преобразоваться в 1.50
    """
    valid_cases = [
        ("event1", "1.50"),
        ("event2", "0.01"),
        ("event3", "100.99"),
        ("event4", "1.5"),
    ]
    
    for event_id, coef in valid_cases:
        event = Event(event_id=event_id, coefficient=Decimal(coef))
        assert event.event_id == event_id
        assert isinstance(event.coefficient, Decimal)
        assert event.coefficient == Decimal(coef).quantize(Decimal("0.01"))

def test_invalid_coefficient_values():
    """
    Проверяем различные невалидные значения коэффициентов
     * Ноль не допускается
     * Отрицательные значения не допускаются
     * Больше двух знаков после запятой
    """
    invalid_cases = [
        ("event_invalid_1", "0"),
        ("event_invalid_2", "-1.00"),
        ("event_invalid_3", "1.501"),
        ("event_invalid_4", "1.567"),
    ]
    
    for event_id, coef in invalid_cases:
        with pytest.raises(ValidationError):
            Event(event_id=event_id, coefficient=Decimal(coef))

def test_non_decimal_coefficient():
    """Проверяем, что нечисловые значения вызывают ошибку"""
    with pytest.raises(ValidationError):
        Event(event_id="event_invalid_5", coefficient="abc")

def test_optional_fields():
    """Проверяем, что все поля кроме event_id опциональны"""
    event = Event(event_id="event_minimal")
    assert event.event_id == "event_minimal"
    assert event.coefficient is None
    assert event.deadline is None
    assert event.state is None
