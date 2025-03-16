from typing import Annotated, List

from fastapi import APIRouter, Path, Query, status

from src.di.container import BetServiceDep, EventServiceDep
from src.domain.entity import BetRequest, BetResponse, Event

router = APIRouter(
    prefix="/api/v1",
    tags=["bets"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Resource not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@router.get(
    "/events", 
    response_model=List[Event],
    summary="Получить доступные события",
    response_description="Список событий доступных для ставок",
    status_code=status.HTTP_200_OK,
)
async def get_available_events(
    service: EventServiceDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Максимальное количество событий для возврата")] = 50,
    offset: Annotated[int, Query(ge=0, description="Количество пропускаемых событий")] = 0,
) -> List[Event]:
    """
    Получение списка активных событий для ставок.
    
    Возвращает постраничный список событий, которые активны и доступны для ставок.
    """
    available_events: List[Event] = await service.get_active_events(limit=limit, offset=offset)
    return available_events


@router.post(
    "/bets", 
    response_model=BetResponse,
    summary="Создать новую ставку",
    response_description="Информация о созданной ставке",
    status_code=status.HTTP_201_CREATED,
)
async def create_bet(
    bet_in: BetRequest,
    service: BetServiceDep,
) -> BetResponse:
    """
    Создание новой ставки на событие.
    
    Создает новую ставку на указанное событие с указанной суммой.
    
    Raises:
        404: Если событие не найдено или недоступно
        422: Если данные ставки недействительны
    """
    new_bet: BetResponse = await service.create_bet(bet_in)
    return new_bet


@router.get(
    "/bets", 
    response_model=List[BetResponse],
    summary="Получить все ставки",
    response_description="Список всех размещенных ставок",
    status_code=status.HTTP_200_OK,
)
async def get_all_bets(
    service: BetServiceDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Максимальное количество ставок для возврата")] = 50,
    offset: Annotated[int, Query(ge=0, description="Количество пропускаемых ставок")] = 0,
    status: Annotated[str, Query(description="Фильтрация ставок по статусу")] = None,
) -> List[BetResponse]:
    """
    Получение истории всех ставок с постраничной навигацией.
    
    Возвращает список всех размещенных ставок с возможностью фильтрации по статусу.
    """
    bets: List[BetResponse] = await service.get_all_bets(limit=limit, offset=offset, status=status)
    return bets


@router.get(
    "/bets/{bet_id}", 
    response_model=BetResponse,
    summary="Получить ставку по ID",
    response_description="Подробная информация о конкретной ставке",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Ставка не найдена"}},
)
async def get_bet_by_id(
    bet_id: Annotated[int, Path(description="Уникальный идентификатор ставки для получения")],
    service: BetServiceDep,
) -> BetResponse:
    """
    Получение подробной информации о конкретной ставке по ID.
    
    Raises:
        404: Если ставка с указанным ID не найдена
    """
    bet: BetResponse = await service.get_bet_by_id(bet_id)
    return bet
