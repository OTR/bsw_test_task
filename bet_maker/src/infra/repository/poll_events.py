import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends

from src.application.service import BetService
from src.config import settings
from src.di.container import get_bet_service, get_bet_repository, get_event_repository
from src.exception import EventRepositoryConnectionError

# Configure logger
logger = logging.getLogger(__name__)

class EventPoller:
    """
    Background service for polling events from the line provider.
    
    This class implements a proper background task that periodically checks 
    for event status updates and updates related bets accordingly.
    
    Attributes:
        bet_service: Service for bet operations
        poll_interval: Seconds between poll operations
        is_running: Flag indicating if polling is active
    """
    
    def __init__(self, bet_service: BetService):
        """
        Initialize the event poller with required services.
        
        Args:
            bet_service: Service for working with bets
        """
        self.bet_service = bet_service
        self.poll_interval = settings.EVENT_POLL_INTERVAL
        self.is_running = False
        self._task = None
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
        self._backoff_factor = 2
    
    async def start(self):
        """Start the polling background task."""
        if self.is_running:
            logger.warning("EventPoller is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Event polling started with interval: {self.poll_interval}s")
    
    async def stop(self):
        """Stop the polling background task gracefully."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Event polling stopped")
    
    async def _poll_loop(self):
        """Main polling loop that runs until stopped."""
        while self.is_running:
            try:
                await self._do_poll()
                # Reset consecutive errors counter on success
                self._consecutive_errors = 0
                # Use normal interval
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                # Increment consecutive errors counter
                self._consecutive_errors += 1
                
                # Calculate backoff time
                backoff_time = min(
                    settings.EVENT_POLL_INTERVAL * (self._backoff_factor ** self._consecutive_errors),
                    300  # Max 5 minutes backoff
                )
                
                # Log appropriate message based on error type
                if isinstance(e, EventRepositoryConnectionError):
                    logger.warning(
                        f"Line provider service unavailable (attempt {self._consecutive_errors}). "
                        f"Retrying in {backoff_time:.1f}s: {e}"
                    )
                else:
                    logger.exception(
                        f"Error during event polling (attempt {self._consecutive_errors}). "
                        f"Retrying in {backoff_time:.1f}s"
                    )
                
                # Use exponential backoff for retries
                await asyncio.sleep(backoff_time)
    
    async def _do_poll(self):
        """Perform the actual polling operation."""
        updated_count = await self.bet_service.update_bets_status()
        if updated_count > 0:
            logger.info(f"Updated status for {updated_count} bets")
        else:
            logger.debug("No bets needed status updates")


# Singleton instance for the application lifecycle
_poller_instance = None


@asynccontextmanager
async def lifespan_event_polling():
    """
    Context manager for event polling lifecycle.
    
    This function should be used in the FastAPI lifespan to properly
    initialize and clean up the polling mechanism.
    
    Example:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with lifespan_event_polling():
                yield
    """
    global _poller_instance
    
    try:
        # Create database session and repositories
        from src.infra.database.database import get_db_session
        from src.infra.http import HTTPClient
        
        # Get required services manually (can't use FastAPI DI here)
        async with get_db_session() as session:
            http_client = HTTPClient(base_url=settings.LINE_PROVIDER_URL)
            bet_repository = get_bet_repository(session)
            event_repository = get_event_repository(http_client)
            
            # Create bet service
            bet_service = BetService(
                bet_repository=bet_repository,
                event_repository=event_repository
            )
            
            # Create and start poller
            _poller_instance = EventPoller(bet_service)
            await _poller_instance.start()
            
            yield
    finally:
        # Ensure poller is stopped on application shutdown
        if _poller_instance:
            await _poller_instance.stop()
            _poller_instance = None


def get_poller() -> EventPoller:
    """
    Dependency provider for the EventPoller.
    
    Returns:
        The singleton EventPoller instance
    
    Raises:
        RuntimeError: If the poller hasn't been initialized yet
    """
    if not _poller_instance:
        raise RuntimeError(
            "EventPoller not initialized. Make sure to include lifespan_event_polling "
            "in your FastAPI application lifespan."
        )
    return _poller_instance


# Annotated dependency for injection
EventPollerDep = Annotated[EventPoller, Depends(get_poller)]
