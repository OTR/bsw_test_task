from typing import Annotated, List

from fastapi import APIRouter, Query, status

from src.di.container import EventServiceDep
from src.domain.entity import Event


router = APIRouter(tags=["Betting Events"])

@router.get(
    "/events",
    response_model=List[Event],
    summary="Получить активные события",
    response_description="Список активных событий доступных для ставок",
    status_code=status.HTTP_200_OK,
    responses={
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail":[
                            {
                                "type":"int_parsing",
                                "loc":["query","offset"],
                                "msg":"Input should be a valid integer, unable to parse string as an integer",
                                "input":"fet"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def get_available_events(
    service: EventServiceDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Максимальное количество событий для возврата")] = 50,
    offset: Annotated[int, Query(ge=0, description="Количество пропускаемых событий")] = 0,
) -> List[Event]:
    """
    Получение списка активных событий доступных для ставок.

    Args:
        service: Сервис для работы с событиями
        limit: Максимальное количество событий для возврата
        offset: Количество пропускаемых событий
    
    Returns:
        List[Event]: Постраничный список событий, которые активны и доступны для ставок    
    """
    available_events: List[Event] = await service.get_active_events(limit=limit, offset=offset)
    return available_events
