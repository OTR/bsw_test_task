from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from src.domain.entity import Bet 
from src.domain.vo import BetStatus


class BaseBetRepository(ABC):
    
    @abstractmethod
    async def get_all(self) -> List[Bet]:
        """
        Retrieves all bets from the repository.
        
        Returns:
            A list of Bet entities
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, bet_id: int) -> Bet:
        """
        Retrieves a specific bet by its ID.
        
        Args:
            bet_id: The unique identifier of the bet to retrieve
            
        Returns:
            The Bet entity if found
            
        Raises:
            BetNotFoundError: If no bet with the specified ID exists
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def get_by_status(self, status: BetStatus) -> List[Bet]:
        """
        Retrieves all bets with a specific status.
        
        Args:
            status: The status to filter by
            
        Returns:
            A list of Bet entities with the specified status
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass

    @abstractmethod
    async def get_by_event_id(self, event_id: int) -> List[Bet]:
        """
        Retrieves all bets associated with a specific event.
        
        Args:
            event_id: The unique identifier of the event
            
        Returns:
            A list of Bet entities associated with the specified event
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def create(self, bet: Bet) -> Bet:
        """
        Creates a new bet in the repository.
        
        Args:
            bet: The Bet entity to create
            
        Returns:
            The created Bet entity with its assigned ID
            
        Raises:
            BetCreationError: If the bet couldn't be created
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def update_status(self, bet_id: int, new_status: BetStatus) -> Bet:
        """
        Updates the status of a specific bet.
        
        Args:
            bet_id: The unique integer identifier of the bet to update
            new_status: The new status to set
            
        Returns:
            The updated Bet entity
            
        Raises:
            BetNotFoundError: If no bet with the specified ID exists
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def filter_bets(
        self,
        event_id: Optional[int] = None,
        status: Optional[BetStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> List[Bet]:
        """
        Retrieves bets that match the specified filters.
        
        Args:
            event_id: Filter by event ID (integer), if provided
            status: Filter by bet status, if provided
            created_after: Only include bets created after this time, if provided
            created_before: Only include bets created before this time, if provided
            
        Returns:
            A list of Bet entities matching the specified filters
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
    
    @abstractmethod
    async def exists(self, bet_id: int) -> bool:
        """
        Checks if a bet with the specified ID exists.
        
        Args:
            bet_id: The unique identifier of the bet to check
            
        Returns:
            True if a bet with the specified ID exists, False otherwise
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the data source
        """
        pass
