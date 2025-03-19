from typing import List

from fastapi import APIRouter, Path, status

from src.di.container import EventServiceDep
from src.domain.entity import CreateEventRequest, CreateEventResponse, EventResponse, Event
from src.exception import EventAlreadyExistsError

router = APIRouter(tags=["Betting Events"])


@router.get(
    '/events',
    response_model=List[EventResponse],
    summary="Получить все события",
    responses={
        200: {"description": "Список всех событий"}
    }
)
async def get_events(
    service: EventServiceDep
) -> List[EventResponse]:
    """
    Получает все существующие события, в том числе неактивные.
    
    Args:
        service: Сервис событий
        
    Returns:
        Список всех существующих событий
    """
    events: List[Event] = await service.get_all_events()
    return [EventResponse.from_domain(event) for event in events]


@router.post(
    '/events',
    response_model=CreateEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое событие",
    responses={
        201: {
            "description": "Событие успешно создано",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "event_id": 0
                    }
                }
            }
        },
        400: {
            "description": "Неправильные данные для создания события",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 400,
                            "message": "Срок события (1742709198) должен быть в будущем. Текущее время: 1742712593",
                            "error_type": "InvalidEventDeadline"
                        }
                    }
                }
            }
        },
        409: {
            "description": "Событие с таким ID уже существует",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 409,
                            "message": "Событие с `event_id` = 1 уже существует",
                            "error_type": "EventAlreadyExists"
                        }
                    }
                }
            }
        }
    }
)
async def create_event(
    service: EventServiceDep,
    event_dto: CreateEventRequest
) -> CreateEventResponse:
    """
    Создает новое событие для ставок.

    Args:
        event_dto: Данные нового события, включая коэффициент и срок
        service: Сервис событий

    Returns:
        Ответ с информацией о созданном событии
    """
    event: Event = event_dto.to_domain()

    if await service.event_exists(event.event_id):
        raise EventAlreadyExistsError(event.event_id)

    created_event: Event = await service.create_event(event)

    return CreateEventResponse(
        success=True,
        event_id=created_event.event_id
    )


@router.put(
    '/events/{event_id}',
    response_model=CreateEventResponse,
    summary="Обновить существующее событие",
    responses={
        200: {
            "description": "Событие успешно обновлено",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "event_id": 21
                    }
                }
            }
        },
        400: {
            "description": "Неверные данные для обновления события",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 400,
                            "message": "ID события в пути должен совпадать с ID в теле запроса",
                            "error_type": "IdMismatch"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Событие по ID не найдено",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 404,
                            "message": "Событие с `event_id` = 21 не найдено",
                            "error_type": "EventNotFound"
                        }
                    }
                }
            }
        }
    }
)
async def update_event(
    service: EventServiceDep,
    event_dto: CreateEventRequest,
    event_id: int = Path(ge=0, description="ID события для обновления")
) -> CreateEventResponse:
    """
    Обновляет существующее событие для ставок.

    Args:
        event_dto: Обновленные данные события
        service: Сервис событий
        event_id: ID события для обновления
    
    Returns:
        Ответ с информацией об обновленном событии

    Raises:
        IdMismatchError: Если ID в пути не совпадает с ID в теле запроса
        EventNotFoundError: Если событие с указанным ID не найдено
    """
    if event_id != event_dto.event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "ID события в пути должен совпадать с ID в теле запроса",
                    "error_type": "IdMismatch"
                }
            }
        )

    if not await service.event_exists(event_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "message": f"Событие с `event_id` = {event_id} не найдено",
                    "error_type": "EventNotFound"
                }
            }
        )

    event: Event = event_dto.to_domain()

    updated_event: Event = await service.update_event(event)

    return CreateEventResponse(
        success=True,
        event_id=updated_event.event_id
    )


@router.get(
    '/events/active',
    response_model=List[EventResponse],
    summary="Получить все активные события",
    responses={
        200: {"description": "Список активных событий"}
    })
async def get_active_events(
    service: EventServiceDep
) -> List[EventResponse]:
    """
    Получает все активные события на которые можно сделать ставку.
    
    Активные события - это те, которые:
    1. Имеют статус равный `NEW`
    2. `deadline` ещё не наступил, т.е. больше чем текущее время

    Args:
        service: Сервис событий
        
    Returns:
        Список активных событий
    """
    events: List[Event] = await service.get_active_events()
    return [EventResponse.from_domain(event) for event in events]


@router.get(
    '/events/{event_id}',
    response_model=EventResponse,
    summary="Получить событие по ID",
    responses={
        200: {"description": "Событие найдено"},
        400: {
            "description": "Неверный ID события",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 400,
                            "message": "[{'type': 'int_parsing', 'loc': ('path', 'event_id'), 'msg': 'Input should be a valid integer, unable to parse string as an integer', 'input': 'abcd'}]",
                            "error_type": "RequestValidationError"
                        }
                    }
                }
            }
        },
        404: {
            "description": "Событие по ID не найдено",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 404,
                            "message": "Событие с `event_id` = 123 не найдено",
                            "error_type": "EventNotFound"
                        }
                    }
                }
            }
        }
    })
async def get_event_by_id(
    service: EventServiceDep,
    event_id: int = Path(ge=0, description="ID события для получения")
) -> EventResponse:
    """
    Получает событие по его ID.

    Args:
        service: Сервис событий
        event_id: ID события для получения
        
    Returns:
        Данные события, если найдено

    Raises:
        404: Если событие по ID не найдено
    """
    event: Event = await service.get_event(event_id)
    return EventResponse.from_domain(event)

