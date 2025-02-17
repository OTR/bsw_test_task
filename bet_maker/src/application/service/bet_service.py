from dataclasses import dataclass
from datetime import datetime
from typing import List

from src.domain.entity import Bet, BetRequest, BetResponse, Event
from src.domain.repository import BaseBetRepository, BaseEventRepository
from src.domain.vo import BetStatus
from src.exception import BetCreationError, EventNotFoundError


@dataclass
class BetService:
    bet_repository: BaseBetRepository
    event_repository: BaseEventRepository

    async def get_all_bets(self) -> List[BetResponse]:
        """
        Retrieves all bets from the repository.
        
        Returns:
            A list of BetResponse objects representing all bets
        """
        bets: List[Bet] = await self.bet_repository.get_all()
        return [BetResponse.model_validate(bet) for bet in bets]
    
    async def get_bet_by_id(self, bet_id: int) -> BetResponse:
        """
        Retrieves a specific bet by its ID.
        
        Args:
            bet_id: The unique identifier of the bet
            
        Returns:
            A BetResponse object representing the found bet
            
        Raises:
            BetNotFoundError: If no bet with the given ID exists
        """
        bet: Bet = await self.bet_repository.get_by_id(bet_id)
        return BetResponse.model_validate(bet)
    
    async def get_bets_by_event(self, event_id: int) -> List[BetResponse]:
        """
        Retrieves all bets for a specific event.
        
        Args:
            event_id: The unique identifier of the event
            
        Returns:
            A list of BetResponse objects representing all bets for that event
        """
        bets: List[Bet] = await self.bet_repository.get_by_event_id(event_id)
        return [BetResponse.model_validate(bet) for bet in bets]
    
    async def get_bets_by_status(self, status: BetStatus) -> List[BetResponse]:
        """
        Retrieves all bets with a specific status.
        
        Args:
            status: The status to filter by
            
        Returns:
            A list of BetResponse objects representing all bets with that status
        """
        bets: List[Bet] = await self.bet_repository.get_by_status(status)
        return [BetResponse.model_validate(bet) for bet in bets]
    
    async def create_bet(self, bet_request: BetRequest) -> BetResponse:
        """
        Creates a new bet for an event.
        
        Args:
            bet_request: The bet request containing event ID and amount
            
        Returns:
            A BetResponse object representing the newly created bet
            
        Raises:
            BetCreationError: If the bet cannot be created due to invalid event or other constraints
        """
        event_id = bet_request.event_id
        amount = bet_request.amount
        
        try:
            event: Event = await self.event_repository.get_by_id(event_id)
        except EventNotFoundError as e:
            raise BetCreationError(f"Cannot create bet: {str(e)}")
            
        if not event.status.is_active:
            raise BetCreationError(f"Cannot create bet: Event with ID {event_id} is already finished")
        
        current_time = int(datetime.now().timestamp())
        if event.deadline < current_time:
            raise BetCreationError(f"Cannot create bet: Event with ID {event_id} deadline has passed")
        
        bet: Bet = Bet(
            bet_id=0,  # Temporary ID, will be assigned by the repository
            event_id=event_id,
            amount=amount,
            status=BetStatus.PENDING,
            created_at=datetime.now()
        )
        
        created_bet: Bet = await self.bet_repository.create(bet)
        return BetResponse.model_validate(created_bet)
    
    async def update_bets_status(self) -> int:
        """
        Updates the status of all pending bets based on finished event statuses.
        
        Args:
            event: Optional specific event to update bets for. If None, updates all bets.
            
        Returns:
            The number of bets that were updated
        """
        all_events: List[Event] = await self.event_repository.get_all()
        
        finished_events = {
            e.event_id: e.status for e in all_events 
            if e.status.is_finished
        }
        
        if not finished_events:
            return 0
        
        updated_count: int = 0
        for event_id, event_status in finished_events.items():
            bets: List[Bet] = await self.bet_repository.get_by_event_id(event_id)
            pending_bets = [bet for bet in bets if bet.status == BetStatus.PENDING]
            
            # TODO: bulk update status to avoid N+1 queries
            for bet in pending_bets:
                new_status = BetStatus.from_event_state(str(event_status))
                if new_status != BetStatus.PENDING:
                    await self.bet_repository.update_status(bet.bet_id, new_status)
                    updated_count += 1

        return updated_count
