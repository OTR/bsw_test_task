import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends

from src.application.service import BetService
from src.config import settings
from src.di.container import get_bet_service, get_bet_repository, get_event_repository
from src.exception import EventRepositoryConnectionError

logger = logging.getLogger(__name__)


class EventPoller:
    """
    Фоновый сервис для опроса сервиса событий.
    
    Реализует фоновую задачу, которая периодически проверяет обновления статусов 
    событий и обновляет связанные ставки.
    
    Attributes:
        bet_service: Сервис для операций со ставками
        poll_interval: Интервал между опросами в секундах
        is_running: Флаг, указывающий активен ли опрос
    """
    
    def __init__(self, bet_service: BetService):
        """
        Инициализация сервиса опроса событий.
        
        Args:
            bet_service: Сервис для работы со ставками
        """
        self.bet_service = bet_service
        self.poll_interval = settings.EVENT_POLL_INTERVAL
        self.is_running = False
        self._task = None
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
        self._backoff_factor = 2
    
    async def start(self):
        """Запуск фоновой задачи опроса."""
        if self.is_running:
            logger.warning("Сервис опроса событий уже запущен")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Опрос событий запущен с интервалом: {self.poll_interval} с")
    
    async def stop(self):
        """Корректная остановка фоновой задачи опроса."""
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
        logger.info("Опрос событий остановлен")
    
    async def _poll_loop(self):
        """Основной цикл опроса, работающий до остановки."""
        while self.is_running:
            try:
                await self._do_poll()
                self._consecutive_errors = 0
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                self._consecutive_errors += 1
                
                backoff_time = min(
                    settings.EVENT_POLL_INTERVAL * (self._backoff_factor ** self._consecutive_errors),
                    300  # Максимальная задержка 5 минут
                )
                
                if isinstance(e, EventRepositoryConnectionError):
                    logger.warning(
                        f"Сервис событий недоступен (попытка {self._consecutive_errors}). "
                        f"Повтор через {backoff_time:.1f}с: {e}"
                    )
                else:
                    logger.exception(
                        f"Ошибка при запросе событий (попытка {self._consecutive_errors}). "
                        f"Повтор через {backoff_time:.1f}с"
                    )
                
                await asyncio.sleep(backoff_time)
    
    async def _do_poll(self):
        """Выполнение операции опроса."""
        updated_count = await self.bet_service.update_bets_status()
        if updated_count > 0:
            logger.info(f"Обновлен статус для {updated_count} ставок")
        else:
            logger.debug("Нет ставок, требующих обновления статуса")


_poller_instance = None


@asynccontextmanager
async def lifespan_event_polling():
    """
    Эта функция должна использоваться в lifespan FastAPI.
    """
    global _poller_instance
    
    try:
        from src.infra.database.database import get_db_session
        from src.infra.http import HTTPClient
        
        async with get_db_session() as session:
            http_client = HTTPClient(base_url=settings.LINE_PROVIDER_URL)
            bet_repository = get_bet_repository(session)
            event_repository = get_event_repository(http_client)
            
            bet_service = BetService(
                bet_repository=bet_repository,
                event_repository=event_repository
            )
            
            _poller_instance = EventPoller(bet_service)
            await _poller_instance.start()
            
            yield
    finally:
        if _poller_instance:
            await _poller_instance.stop()
            _poller_instance = None


def get_poller() -> EventPoller:
    """
    Raises:
        RuntimeError: Если сервис опроса еще не инициализирован
    """
    if not _poller_instance:
        raise RuntimeError(
            "Сервис опроса событий не инициализирован. Убедитесь, что lifespan_event_polling "
            "включен в жизненный цикл приложения FastAPI."
        )
    return _poller_instance


EventPollerDep = Annotated[EventPoller, Depends(get_poller)]  # TODO: move to container
