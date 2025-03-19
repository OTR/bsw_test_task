import logging
from functools import lru_cache
from typing import Annotated, AsyncGenerator, Callable, Dict, Type, TypeVar, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.service import BetService, EventService
from src.config import settings
from src.domain.repository import BaseBetRepository, BaseEventRepository
from src.infra.database.database import get_db_session
from src.infra.http import HTTPClient
from src.infra.repository import SQLAlchemyBetRepository, RemoteEventRepository

logger = logging.getLogger(__name__)
T = TypeVar('T')


@lru_cache(maxsize=1)
def get_http_client() -> HTTPClient:
    """
    Получение HTTP-клиента для запросов к внешним сервисам.
    
    Returns:
        Кэшированный экземпляр HTTPClient
    """
    logger.debug(f"Создание HTTPClient с базовым URL: {settings.LINE_PROVIDER_URL}")
    return HTTPClient(base_url=settings.LINE_PROVIDER_URL)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Получение сессии базы данных.
    
    Yields:
        Асинхронная сессия базы данных
    """
    async with get_db_session() as session:
        logger.debug("Сессия базы данных создана")
        yield session
        logger.debug("Сессия базы данных закрыта")


def get_bet_repository(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> BaseBetRepository:
    """
    Получение репозитория ставок.
    
    Args:
        session: Сессия базы данных для операций
        
    Returns:
        Реализация интерфейса BaseBetRepository
    """
    return SQLAlchemyBetRepository(session)


def get_event_repository(
    http_client: Annotated[HTTPClient, Depends(get_http_client)]
) -> BaseEventRepository:
    """
    Получение репозитория событий.
    
    Args:
        http_client: HTTP-клиент для запросов к провайдеру
        
    Returns:
        Реализация интерфейса BaseEventRepository
    """
    return RemoteEventRepository(http_client=http_client)


def get_bet_service(
    bet_repository: Annotated[BaseBetRepository, Depends(get_bet_repository)],
    event_repository: Annotated[BaseEventRepository, Depends(get_event_repository)]
) -> BetService:
    """
    Получение сервиса для работы со ставками.
    
    Args:
        bet_repository: Репозиторий ставок
        event_repository: Репозиторий событий
        
    Returns:
        Экземпляр BetService
    """
    return BetService(bet_repository, event_repository)


def get_event_service(
    event_repository: Annotated[BaseEventRepository, Depends(get_event_repository)],
) -> EventService:
    """
    Получение сервиса для работы с событиями.
    
    Args:
        event_repository: Репозиторий событий
        
    Returns:
        Экземпляр EventService
    """
    return EventService(event_repository)


BetServiceDep = Annotated[BetService, Depends(get_bet_service)]
EventServiceDep = Annotated[EventService, Depends(get_event_service)]


class DependencyRegistry:
    """
    Service locator pattern
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
        Регистрация поставщика зависимости.
        
        Args:
            interface_type: Тип интерфейса для регистрации
            provider: Функция, предоставляющая экземпляры типа
        """
        cls._registry[interface_type] = provider

    @classmethod
    def get_provider(cls, interface_type: Type[T]) -> Callable[..., T]:
        """
        Получение функции-поставщика для указанного типа.
        
        Args:
            interface_type: Тип интерфейса
            
        Returns:
            Функция-поставщик для запрошенного типа
            
        Raises:
            KeyError: Если нет зарегистрированного поставщика
        """
        if interface_type not in cls._registry:
            raise KeyError(f"Нет зарегистрированного поставщика для {interface_type.__name__}")

        return cast(Callable[..., T], cls._registry[interface_type])

    @classmethod
    def get_dependency(cls, interface_type: Type[T]) -> Annotated[T, Depends]:
        """
        Получение зависимости FastAPI для указанного типа.
        
        Args:
            interface_type: Тип интерфейса
            
        Returns:
            Аннотированная зависимость для FastAPI
            
        Raises:
            KeyError: Если нет зарегистрированного поставщика
        """
        provider = cls.get_provider(interface_type)
        return Annotated[interface_type, Depends(provider)]


def get_dependency(
    request: Request,
    dependency_type: Type[T]
) -> T:
    """
    Получение зависимости из текущего запроса.
    
    Args:
        request: Объект текущего запроса
        dependency_type: Тип зависимости
        
    Returns:
        Запрошенный экземпляр зависимости
        
    Raises:
        RuntimeError: Если зависимость не найдена
    """
    provider = DependencyRegistry.get_provider(dependency_type)

    try:
        return request.scope["fastapi_deps"].get(provider)
    except (KeyError, AttributeError):
        raise RuntimeError(
            f"Не удалось найти {dependency_type.__name__} в кэше зависимостей. "
            "Убедитесь, что она правильно внедрена в функцию маршрута."
        )
