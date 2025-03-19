class LineProviderError(Exception):
    """Базовый класс для всех ошибок Line Provider"""


class EventNotFoundError(LineProviderError):

    def __init__(self, event_id: int):
        super().__init__(f"Событие с `event_id` = {event_id} не найдено")
        self.event_id: int = event_id


class EventAlreadyExistsError(LineProviderError):
    """Возникает при попытке создать уже существующее событие"""

    def __init__(self, event_id: int):
        super().__init__(f"Событие с `event_id` = {event_id} уже существует")
        self.event_id: int = event_id


class InvalidEventDeadlineError(LineProviderError):
    """
    Возникает при недействительном сроке события.
    
    Это может произойти по двум причинам:
    1. Срок не является положительным числом (<= 0)
    2. Срок не в будущем (<= текущее время)
    """
    def __init__(self, deadline: int, current_time: int):
        if deadline <= 0:
            message = f"Срок события ({deadline}) недействителен. Должен быть положительным Unix-временем."
        else:
            message = f"Срок события ({deadline}) должен быть в будущем. Текущее время: {current_time}"

        self.deadline = deadline
        self.current_time = current_time
        super().__init__(message)
