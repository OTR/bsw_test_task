from enum import Enum


class EventStatus(str, Enum):
    """
    Статусы события для ставок

    Values:
        NEW - новое событие
        FINISHED_WIN - событие завершилось победой
        FINISHED_LOSE - событие завершилось поражением
    """
    NEW: str = "NEW"
    FINISHED_WIN: str = "FINISHED_WIN"
    FINISHED_LOSE: str = "FINISHED_LOSE"
