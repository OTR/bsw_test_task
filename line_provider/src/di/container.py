from typing import Any, Callable, Dict, Type, TypeVar

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.application.service.event_service import EventService
from src.domain.repository import BaseEventRepository
from src.infra.repository.in_memory_event_repository import InMemoryEventRepository
from functools import lru_cache
from typing import Annotated, Type

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.domain.repository import BaseEventRepository
from src.application.service import EventService
from src.infra.repository import InMemoryEventRepository



class LineProviderSettings(BaseSettings):
    """Configuration settings for the line provider service."""
    
    # Repository configuration
    repository_type: str = "memory"  # Default to in-memory repository
    
    # Additional configuration parameters can be added here

    model_config = SettingsConfigDict(
        env_prefix="LINE_PROVIDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Type for caching dependencies
T = TypeVar("T")

# Cache for dependency instances
_dependencies_cache: Dict[str, Any] = {}

# Settings instance
_settings: LineProviderSettings | None = None


def get_settings() -> LineProviderSettings:
    """
    Get application settings.
    
    Returns:
        LineProviderSettings: Application settings
    """
    global _settings
    if _settings is None:
        _settings = LineProviderSettings()
    return _settings


def get_or_create_dependency(name: str, factory: Callable[[], T]) -> T:
    """
    Get a dependency from the cache or create it if it doesn't exist.
    
    Args:
        name: Name of the dependency
        factory: Factory function to create the dependency
        
    Returns:
        Dependency instance
    """
    global _dependencies_cache
    if name not in _dependencies_cache:
        _dependencies_cache[name] = factory()
    return _dependencies_cache[name]


def get_event_repository() -> BaseEventRepository:
    """
    Get the configured event repository.
    
    Returns:
        BaseEventRepository: Repository instance
    """
    def create_repository() -> BaseEventRepository:
        settings = get_settings()
        
        # We can easily extend this to support different repository types
        if settings.repository_type == "memory":
            return InMemoryEventRepository()
        else:
            raise ValueError(
                f"Invalid repository type: {settings.repository_type}. "
                f"Valid options are: memory"
            )
    
    return get_or_create_dependency("event_repository", create_repository)


def get_event_service(
    repository: BaseEventRepository = Depends(get_event_repository)
) -> EventService:
    """
    Get the event service.
    
    Args:
        repository: Event repository
        
    Returns:
        EventService: Event service instance
    """
    return EventService(repository=repository)


# Aliases for type hints in route dependencies
EventServiceDep = Depends(get_event_service)


def init_container() -> None:
    """Initialize the dependency injection container."""
    # Pre-load dependencies at startup if needed
    pass
"""Dependency injection container for the application."""



class Settings(BaseSettings):
    """Application configuration settings."""
    model_config = SettingsConfigDict(
        env_prefix="LINE_PROVIDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Repository configuration
    repository_type: str = "memory"  # Options: memory, db (future)


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Returns:
        Application settings instance
    """
    return Settings()


def get_event_repository() -> BaseEventRepository:
    """
    Get event repository instance based on configuration.
    
    Returns:
        Event repository implementation
    """
    settings = get_settings()
    
    # Map repository types to their implementations
    repository_map: dict[str, Type[BaseEventRepository]] = {
        "memory": InMemoryEventRepository,
        # Add more repository implementations here
    }
    
    repository_class = repository_map.get(settings.repository_type.lower())
    if not repository_class:
        raise ValueError(
            f"Invalid repository type: {settings.repository_type}. "
            f"Valid options are: {', '.join(repository_map.keys())}"
        )
    
    return InMemoryEventRepository()


def get_event_service(
    repository: Annotated[BaseEventRepository, Depends(get_event_repository)]
) -> EventService:
    """
    Get event service instance.
    
    Args:
        repository: Event repository dependency
    
    Returns:
        Event service instance
    """
    return EventService(repository)


# FastAPI dependency types
EventServiceDep = Annotated[EventService, Depends(get_event_service)]


def init_container() -> None:
    """Initialize the dependency injection container and validate configuration."""
    # Validate settings on startup
    get_settings()
    
    # Pre-initialize repositories if needed
    get_event_repository()

