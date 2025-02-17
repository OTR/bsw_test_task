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
    summary="Get available events",
    response_description="List of events available for betting",
    status_code=status.HTTP_200_OK,
)
async def get_available_events(
    service: EventServiceDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of events to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of events to skip")] = 0,
) -> List[Event]:
    """
    Retrieve a list of active events available for betting.
    
    Returns a paginated list of events that are currently active and available
    for placing bets.
    """
    available_events: List[Event] = await service.get_active_events(limit=limit, offset=offset)
    return available_events


@router.post(
    "/bets", 
    response_model=BetResponse,
    summary="Create new bet",
    response_description="Newly created bet details",
    status_code=status.HTTP_201_CREATED,
)
async def create_bet(
    bet_in: BetRequest,
    service: BetServiceDep,
) -> BetResponse:
    """
    Place a new bet on an event.
    
    Creates a new bet on the specified event with the provided amount.
    Returns the created bet information including its unique identifier.
    
    Raises:
        404: If the event is not found or not available
        422: If the bet data is invalid
    """
    new_bet: BetResponse = await service.create_bet(bet_in)
    return new_bet


@router.get(
    "/bets", 
    response_model=List[BetResponse],
    summary="Get all bets",
    response_description="List of all placed bets",
    status_code=status.HTTP_200_OK,
)
async def get_all_bets(
    service: BetServiceDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of bets to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Number of bets to skip")] = 0,
    status: Annotated[str, Query(description="Filter bets by status")] = None,
) -> List[BetResponse]:
    """
    Retrieve a paginated history of all bets.
    
    Returns all bets placed in the system, with optional filtering by status.
    Results are paginated using limit and offset parameters.
    """
    bets: List[BetResponse] = await service.get_all_bets(limit=limit, offset=offset, status=status)
    return bets


@router.get(
    "/bets/{bet_id}", 
    response_model=BetResponse,
    summary="Get bet by ID",
    response_description="Detailed information about a specific bet",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Bet not found"}},
)
async def get_bet_by_id(
    bet_id: Annotated[int, Path(description="The unique identifier of the bet to retrieve")],
    service: BetServiceDep,
) -> BetResponse:
    """
    Retrieve detailed information about a specific bet.
    
    Gets the complete information for a single bet identified by its unique ID.
    
    Raises:
        404: If the bet with the specified ID is not found
    """
    bet: Bet = await service.get_bet_by_id(bet_id)
    return bet
