from typing import List, Union, Optional
from datetime import datetime

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.domain.entity.bet import Bet, BetRequest, BetResponse
from src.domain.repository.base_bet_repository import BaseBetRepository
from src.domain.vo.bet_status import BetStatus
from src.infra.database.bet_model import BetModel
from src.exception import (
    BetNotFoundError,
    BetRepositoryConnectionError,
    BetCreationError
)


class SQLAlchemyBetRepository(BaseBetRepository):
    
    def __init__(self, session: AsyncSession):
        self._session: AsyncSession = session

    async def get_all(self) -> List[Bet]:
        """
        Retrieves all bets from the database.
        
        Returns:
            A list of Bet domain entities
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            # Use the modern select() style with order_by for consistent results
            stmt = select(BetModel).order_by(BetModel.created_at.desc())
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            # Convert SQLAlchemy errors to domain-specific errors
            raise BetRepositoryConnectionError(f"Failed to retrieve bets: {str(e)}")
    
    async def get_by_id(self, bet_id: Union[int, str]) -> Bet:
        """
        Retrieves a specific bet by its unique identifier.
        
        Args:
            bet_id: The unique identifier of the bet to retrieve
            
        Returns:
            The Bet domain entity if found
            
        Raises:
            BetNotFoundError: If the bet with the specified ID doesn't exist
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            # Use scalar_one_or_none for efficient fetching with proper error handling
            stmt = select(BetModel).where(BetModel.bet_id == bet_id)
            result = await self._session.execute(stmt)
            bet_model = result.scalar_one_or_none()
            
            if bet_model is None:
                raise BetNotFoundError(f"Bet with ID {bet_id} not found")
            
            return self._to_domain_entity(bet_model)
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Failed to retrieve bet: {str(e)}")
    
    async def create(self, bet: Bet) -> Bet:
        """
        Creates a new bet in the database.
        
        Args:
            bet: The Bet domain entity to create
            
        Returns:
            The created Bet domain entity with assigned ID
            
        Raises:
            BetCreationError: If the bet couldn't be created
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            bet_model = self._to_db_model(bet)
            
            self._session.add(bet_model)
            await self._session.commit()
            await self._session.refresh(bet_model)
            
            return self._to_domain_entity(bet_model)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetCreationError(f"Failed to create bet: {str(e)}")
        except Exception as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Unexpected error: {str(e)}")
    
    async def get_by_event_id(self, event_id: Union[int, str]) -> List[Bet]:
        """
        Retrieves all bets associated with a specific event.
        
        Args:
            event_id: The unique identifier of the event
            
        Returns:
            A list of Bet domain entities associated with the event
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            stmt = select(BetModel).where(BetModel.event_id == str(event_id))
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Failed to retrieve bets by event ID: {str(e)}")
    
    async def get_by_status(self, status: BetStatus) -> List[Bet]:
        """
        Retrieves all bets with a specific status.
        
        Args:
            status: The status to filter by
            
        Returns:
            A list of Bet domain entities with the specified status
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            stmt = select(BetModel).where(BetModel.status == status)
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Failed to retrieve bets by status: {str(e)}")
    
    async def update_status(self, bet_id: Union[int, str], new_status: BetStatus) -> Bet:
        """
        Updates the status of a specific bet.
        
        Args:
            bet_id: The unique identifier of the bet to update
            new_status: The new status to set
            
        Returns:
            The updated Bet domain entity
            
        Raises:
            BetNotFoundError: If the bet with the specified ID doesn't exist
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            exists = await self.exists(bet_id)
            if not exists:
                raise BetNotFoundError(f"Bet with ID {bet_id} not found")
            
            stmt = (
                update(BetModel)
                .where(BetModel.bet_id == bet_id)
                .values(status=new_status)
            )
            await self._session.execute(stmt)
            
            get_stmt = select(BetModel).where(BetModel.bet_id == bet_id)
            result = await self._session.execute(get_stmt)
            updated_bet = result.scalar_one_or_none()
            
            if updated_bet is None:
                raise BetNotFoundError(f"Bet with ID {bet_id} not found after update")
                
            await self._session.commit()
                
            return self._to_domain_entity(updated_bet)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Failed to update bet status: {str(e)}")
    
    async def bulk_update_status(self, bet_ids: List[Union[int, str]], new_status: BetStatus) -> int:
        """
        Updates the status of multiple bets in a single operation.
        
        Args:
            bet_ids: The unique identifiers of the bets to update
            new_status: The new status to set
            
        Returns:
            The number of bets that were updated
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            stmt = (
                update(BetModel)
                .where(BetModel.bet_id.in_(bet_ids))
                .values(status=new_status)
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            
            return result.rowcount
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Failed to update bet statuses: {str(e)}")
    
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
            event_id: Filter by event ID, if provided
            status: Filter by bet status, if provided
            created_after: Only include bets created after this time, if provided
            created_before: Only include bets created before this time, if provided
            
        Returns:
            A list of Bet domain entities matching the specified filters
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            filters = []
            if event_id is not None:
                filters.append(BetModel.event_id == str(event_id))
            
            if status is not None:
                filters.append(BetModel.status == status)
                
            if created_after is not None:
                filters.append(BetModel.created_at >= created_after)
                
            if created_before is not None:
                filters.append(BetModel.created_at <= created_before)
            
            stmt = select(BetModel)
            if filters:
                stmt = stmt.where(and_(*filters))
            
            result = await self._session.execute(stmt)
            bet_models = result.scalars().all()
            
            return [self._to_domain_entity(bet_model) for bet_model in bet_models]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Failed to filter bets: {str(e)}")
    
    async def exists(self, bet_id: int) -> bool:
        """
        Checks if a bet with the specified ID exists.
        
        Args:
            bet_id: The unique identifier of the bet to check
            
        Returns:
            True if a bet with the specified ID exists, False otherwise
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            stmt = select(BetModel.bet_id).where(BetModel.bet_id == bet_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Failed to check if bet exists: {str(e)}")
    
    async def update_bets(self, bets: List[Bet]) -> List[Bet]:
        """
        Updates multiple bets in a single operation.
        
        Args:
            bets: List of bet entities with updated values
            
        Returns:
            List of updated bet entities
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            updated_bets = []
            
            for bet in bets:
                stmt = (
                    update(BetModel)
                    .where(BetModel.bet_id == bet.bet_id)
                    .values(
                        event_id=str(bet.event_id),
                        amount=bet.amount,
                        status=bet.status
                    )
                )
                await self._session.execute(stmt)
                
                updated_bets.append(bet)
            
            await self._session.commit()
            
            return updated_bets
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetRepositoryConnectionError(f"Failed to update bets: {str(e)}")
    
    async def save(self, bet_request: BetRequest) -> BetResponse:
        """
        Save a new bet from a BetRequest DTO.
        
        Args:
            bet_request: The bet request data from the API
            
        Returns:
            A BetResponse containing the saved bet data
            
        Raises:
            BetCreationError: If the bet couldn't be created
        """
        try:
            new_bet_model = BetModel(
                event_id=str(bet_request.event_id),
                amount=bet_request.amount,
                status=BetStatus.PENDING
            )
            
            self._session.add(new_bet_model)
            await self._session.commit()
            await self._session.refresh(new_bet_model)
            
            return BetResponse.model_validate(new_bet_model, from_attributes=True)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise BetCreationError(f"Failed to save bet: {str(e)}")
    
    save_bet = save
    
    async def get_pending_bets(self) -> List[BetResponse]:
        """
        Get all bets with status `PENDING`.
        
        Returns:
            List of pending bets
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            stmt = select(BetModel).where(BetModel.status == BetStatus.PENDING)
            result = await self._session.execute(stmt)
            pending_bets = result.scalars().all()
            
            return [BetResponse.model_validate(bet, from_attributes=True) for bet in pending_bets]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Failed to get pending bets: {str(e)}")
    
    async def get_all_bets(self, limit: int = 100) -> List[BetResponse]:
        """
        Get all bets from database with pagination.
        
        Args:
            limit: Maximum number of bets to return
            
        Returns:
            List of bets up to the specified limit
            
        Raises:
            BetRepositoryConnectionError: If there's an issue connecting to the database
        """
        try:
            stmt = select(BetModel).order_by(BetModel.created_at.desc()).limit(limit)
            result = await self._session.execute(stmt)
            bets = result.scalars().all()
            
            return [BetResponse.model_validate(bet, from_attributes=True) for bet in bets]
        except SQLAlchemyError as e:
            raise BetRepositoryConnectionError(f"Failed to get all bets: {str(e)}")
    
    def _to_domain_entity(self, bet_model: BetModel) -> Bet:
        """
        Converts a database model to a domain entity.
        
        Args:
            bet_model: The database model to convert
            
        Returns:
            The corresponding domain entity
        """
        return Bet(
            bet_id=bet_model.bet_id,
            event_id=bet_model.event_id,
            amount=bet_model.amount,
            status=bet_model.status,
            created_at=bet_model.created_at
        )
    
    def _to_db_model(self, bet: Bet) -> BetModel:
        """
        Converts a domain entity to a database model.
        
        Args:
            bet: The domain entity to convert
            
        Returns:
            The corresponding database model
        """
        bet_model = BetModel(
            event_id=bet.event_id,
            amount=bet.amount,
            status=bet.status
        )
        
        if hasattr(bet, 'bet_id') and bet.bet_id is not None:
            bet_model.bet_id = bet.bet_id
        
        if hasattr(bet, 'created_at') and bet.created_at is not None:
            bet_model.created_at = bet.created_at
        
        return bet_model
