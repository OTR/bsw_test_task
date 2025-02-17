from enum import Enum


class EventStatus(str, Enum):
    """
    Status for betting event

    Values:
        NEW - new event
        FINISHED_WIN - event finished with win
        FINISHED_LOSE - event finished with lose
    """
    NEW: str = "NEW"
    FINISHED_WIN: str = "FINISHED_WIN"
    FINISHED_LOSE: str = "FINISHED_LOSE"
