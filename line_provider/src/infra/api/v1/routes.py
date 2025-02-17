from typing import List

from fastapi import APIRouter, Path, status
from fastapi.responses import JSONResponse

from src.domain.entity import CreateEventRequest, CreateEventResponse, EventResponse, Event
from src.di.container import EventServiceDep
from src.exception import EventAlreadyExistsError


router = APIRouter(tags=["Betting Events"])

@router.post(
    '/event',
    response_model=CreateEventResponse,
    responses={
        201: {"description": "Event created successfully"},
        400: {"description": "Invalid event data"},
        409: {"description": "Event already exists"},
        500: {"description": "Internal server error"}
    }
)
async def create_event(
    service: EventServiceDep,
    event_dto: CreateEventRequest
) -> JSONResponse:
    """
    Create a new betting event.

    Args:
        event_dto: Event data including coefficient and deadline
        service: Event service dependency
    
    Returns:
        JSON response with success status
    """
    event = event_dto.to_domain()
    
    if await service.event_exists(event.event_id):
        raise EventAlreadyExistsError(event.event_id)
        
    created_event = await service.create_event(event)
    
    return JSONResponse(
        content=CreateEventResponse(
            success=True,
            event_id=created_event.event_id
        ).model_dump(),
        status_code=status.HTTP_201_CREATED
    )

@router.put(
    '/event/{event_id}',
    response_model=CreateEventResponse,
    responses={
        200: {"description": "Event updated successfully"},
        400: {"description": "Invalid event data"},
        404: {"description": "Event not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_event(
    service: EventServiceDep,
    event_dto: CreateEventRequest,
    event_id: int = Path(ge=0, description="The ID of the event to update")
) -> JSONResponse:
    """
    Update an existing betting event.

    Args:
        event_dto: Updated event data including coefficient and deadline
        service: Event service dependency
        event_id: ID of the event to update
    
    Returns:
        JSON response with success status
    """
    if event_id != event_dto.event_id:
        return JSONResponse(
            content={"detail": "Event ID in path must match event ID in request body"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if not await service.event_exists(event_id):
        return JSONResponse(
            content={"detail": f"Event with ID {event_id} not found"},
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    event = event_dto.to_domain()
    
    updated_event = await service.update_event(event)
    
    return JSONResponse(
        content=CreateEventResponse(
            success=True,
            event_id=updated_event.event_id
        ).model_dump(),
        status_code=status.HTTP_200_OK
    )


@router.get(
    '/event/{event_id}',
    response_model=EventResponse,
    responses={
        200: {"description": "Event found"},
        404: {"description": "Event not found"}
    })
async def get_event_by_id(
    service: EventServiceDep,
    event_id: int = Path(ge=0, description="The ID of the event to retrieve")
) -> EventResponse:
    """
    Get event by its ID.
    
    Args:
        service: Event service dependency
        event_id: ID of the event to retrieve
        
    Returns:
        Event data if found
    """
    event: Event = await service.get_event(event_id)
    return EventResponse.from_domain(event)


@router.get(
    '/events',
    response_model=List[EventResponse],
    responses={
        200: {"description": "List of all events"}
    })
async def get_events(
    service: EventServiceDep
) -> List[EventResponse]:
    """
    Get all betting events.
    
    Args:
        service: Event service dependency
        
    Returns:
        List of all events in the system
    """
    events: List[Event] = await service.get_all_events()
    return [EventResponse.from_domain(event) for event in events]


@router.get(
    '/events/active',
    response_model=List[EventResponse],
    responses={
        200: {"description": "List of active events"}
    })
async def get_active_events(
    service: EventServiceDep
) -> List[EventResponse]:
    """
    Get all active betting events.
    
    Active events are those that:
    1. Have status = NEW
    2. Have deadline in the future
    
    Args:
        service: Event service dependency
        
    Returns:
        List of active events
    """
    events: List[Event] = await service.get_active_events()
    return [EventResponse.from_domain(event) for event in events]
