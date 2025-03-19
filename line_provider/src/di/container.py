from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.application.service import EventService
from src.domain.repository import BaseEventRepository
from src.infra.repository import InMemoryEventRepository


def get_event_repository() -> BaseEventRepository:
    """
    Получение настроенного репозитория событий.
    
    Returns:
        BaseEventRepository: Экземпляр репозитория
    """
    settings = get_settings()

    if settings.repository_type == "memory":
        return InMemoryEventRepository()
    else:
        raise ValueError(
            f"Неверный тип репозитория: {settings.repository_type}. "
            f"Доступные варианты: memory"
        )


class Settings(BaseSettings):
    """Настройки конфигурации приложения."""

    repository_type: str = "memory"

    model_config = SettingsConfigDict(
        env_prefix="LINE_PROVIDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Получение синглтона настроек приложения.
    
    Returns:
        Экземпляр настроек приложения
    """
    return Settings()


def get_event_service(
    repository: Annotated[BaseEventRepository, Depends(get_event_repository)]
) -> EventService:
    """
    Получение экземпляра сервиса событий.
    
    Args:
        repository: Зависимость репозитория событий
    
    Returns:
        Экземпляр сервиса событий
    """
    return EventService(repository)


def init_container() -> None:
    """Инициализация контейнера внедрения зависимостей и проверка конфигурации."""
    get_settings()
    get_event_repository()


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
