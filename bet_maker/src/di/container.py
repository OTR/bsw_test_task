from typing import Annotated, AsyncGenerator, Callable, Dict, Type, TypeVar, cast
import logging
from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.service import BetService, EventService
from src.config import settings
from src.domain.repository import BaseBetRepository, BaseEventRepository
from src.infra.database.database import get_db_session
from src.infra.http import HTTPClient
from src.infra.repository import SQLAlchemyBetRepository, RemoteEventRepository

# Configure logger
logger = logging.getLogger(__name__)

# Type variable for dependency providers
T = TypeVar('T')


# Cache HTTP client to avoid creating a new instance on every request
@lru_cache(maxsize=1)
def get_http_client() -> HTTPClient:
    """
    Provides a cached HTTP client for making requests to external services.
    
    Returns:
        A cached instance of HTTPClient configured with the line provider URL
    """
    logger.debug(f"Creating HTTPClient with base URL: {settings.LINE_PROVIDER_URL}")
    return HTTPClient(base_url=settings.LINE_PROVIDER_URL)


# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session with proper lifecycle management.
    
    Yields:
        An async database session for accessing the database
    """
    async with get_db_session() as session:
        logger.debug("Database session created")
        yield session
        logger.debug("Database session closed")


# Repository dependencies with proper typing
def get_bet_repository(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> BaseBetRepository:
    """
    Provides a repository for accessing bet data.
    
    Args:
        session: The database session to use for repository operations
        
    Returns:
        An implementation of the BaseBetRepository interface
    """
    return SQLAlchemyBetRepository(session)


def get_event_repository(
    http_client: Annotated[HTTPClient, Depends(get_http_client)]
) -> BaseEventRepository:
    """
    Provides a repository for accessing event data.
    
    Args:
        http_client: HTTP client for making requests to the line provider
        
    Returns:
        An implementation of the BaseEventRepository interface
    """
    return RemoteEventRepository(http_client=http_client)


# Service dependencies
def get_bet_service(
    bet_repository: Annotated[BaseBetRepository, Depends(get_bet_repository)],
    event_repository: Annotated[BaseEventRepository, Depends(get_event_repository)]
) -> BetService:
    """
    Provides a service for working with bets.
    
    Args:
        bet_repository: Repository for accessing bet data
        event_repository: Repository for accessing event data
        
    Returns:
        An instance of the BetService
    """
    return BetService(bet_repository, event_repository)


def get_event_service(
    event_repository: Annotated[BaseEventRepository, Depends(get_event_repository)],
) -> EventService:
    """
    Provides a service for working with events.
    
    Args:
        event_repository: Repository for accessing event data
        
    Returns:
        An instance of the EventService
    """
    return EventService(event_repository)


# Create annotated dependencies for services with improved naming
BetServiceDep = Annotated[BetService, Depends(get_bet_service)]
EventServiceDep = Annotated[EventService, Depends(get_event_service)]


# Factory for creating request-scoped dependencies
class DependencyRegistry:
    """
    Registry for managing and retrieving application dependencies.
    
    This class follows the service locator pattern to provide a central
    registry for application dependencies, while still leveraging FastAPI's
    dependency injection system.
    """
    
    _registry: Dict[Type, Callable] = {
        HTTPClient: get_http_client,
        BaseBetRepository: get_bet_repository,
        BaseEventRepository: get_event_repository,
        BetService: get_bet_service,
        EventService: get_event_service
    }
    
    @classmethod
    def register(cls, interface_type: Type[T], provider: Callable[..., T]) -> None:
        """
        Register a dependency provider for an interface type.
        
        Args:
            interface_type: The type/interface to register
            provider: The callable that provides instances of the type
        """
        cls._registry[interface_type] = provider
        
    @classmethod
    def get_provider(cls, interface_type: Type[T]) -> Callable[..., T]:
        """
        Get the provider function for a specific interface type.
        
        Args:
            interface_type: The type/interface to get the provider for
            
        Returns:
            The provider function for the requested type
            
        Raises:
            KeyError: If no provider is registered for the requested type
        """
        if interface_type not in cls._registry:
            raise KeyError(f"No provider registered for {interface_type.__name__}")
            
        return cast(Callable[..., T], cls._registry[interface_type])
    
    @classmethod
    def get_dependency(cls, interface_type: Type[T]) -> Annotated[T, Depends]:
        """
        Get a FastAPI dependency for a specific interface type.
        
        Args:
            interface_type: The type/interface to get the dependency for
            
        Returns:
            An annotated dependency that can be used with FastAPI
            
        Raises:
            KeyError: If no provider is registered for the requested type
        """
        provider = cls.get_provider(interface_type)
        return Annotated[interface_type, Depends(provider)]


# Request-scoped dependency accessor
def get_dependency(
    request: Request,
    dependency_type: Type[T]
) -> T:
    """
    Get a dependency from the current request scope.
    
    This allows getting dependencies programmatically rather than through
    function parameters, which can be useful in certain scenarios.
    
    Args:
        request: The current request object
        dependency_type: The type of dependency to retrieve
        
    Returns:
        The requested dependency instance
        
    Raises:
        RuntimeError: If the dependency cannot be found
    """
    provider = DependencyRegistry.get_provider(dependency_type)
    
    try:
        # Access FastAPI's dependency cache
        return request.scope["fastapi_deps"].get(provider)
    except (KeyError, AttributeError):
        raise RuntimeError(
            f"Could not find {dependency_type.__name__} in the request's dependency cache. "
            "Make sure it's properly injected in the route function."
        )
