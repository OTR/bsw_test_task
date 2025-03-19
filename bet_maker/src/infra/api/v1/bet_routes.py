from typing import Annotated, List

from fastapi import APIRouter, Path, Query, status

from src.di.container import BetServiceDep
from src.domain.entity import BetRequest, BetResponse

router = APIRouter(tags=["Bets"])


@router.post(
    "/bets",
    response_model=BetResponse,
    summary="Создать новую ставку",
    response_description="Информация о созданной ставке",
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {
            "description": "Event not found or not available",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 404,
                            "message": "Не удалось создать ставку: Невозможно создать ставку: Событие с ID 7 не найдено",
                            "error_type": "BetCreationError"
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                            "type": "value_error",
                            "loc": [
                                "body",
                                "amount"
                            ],
                            "msg": "Value error, Сумма ставки должна иметь ровно 2 знака после запятой",
                            "input": 0.001,
                            "ctx": {
                                "error": {}
                            }
                            }
                        ]
                    }
                }
            }
        }
    }
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
    responses={
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type":"less_than_equal",
                                "loc":["query","limit"],
                                "msg":"Input should be less than or equal to 100",
                                "input":"150","ctx":{"le":100}
                            }
                        ]
                    }
                }
            }
        }
    }
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
    responses={
        404: {
            "description": "Ставка не найдена",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "status_code": 404,
                            "message": "Ставка с ID Ставка с ID 3 не найдена не найдена",
                            "error_type": "BetNotFoundError"
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "greater_than_equal",
                                "loc": ["path", "bet_id"],
                                "msg": "Input should be greater than or equal to 0",
                                "input": "-4",
                                "ctx": {"ge": 0}
                            }
                        ]
                    }
                }
            }
        }
    },
)
async def get_bet_by_id(
    bet_id: Annotated[int, Path(ge=0, description="Уникальный идентификатор ставки для получения")],
    service: BetServiceDep,
) -> BetResponse:
    """
    Получение подробной информации о конкретной ставке по ID.
    
    Args:
        bet_id: Уникальный идентификатор ставки для получения, greater than or equal to 0
    
    Raises:
        404: Если ставка с указанным ID не найдена
    """
    bet: BetResponse = await service.get_bet_by_id(bet_id)
    return bet
