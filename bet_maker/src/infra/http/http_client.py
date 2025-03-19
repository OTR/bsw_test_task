from typing import Any, Dict, Optional, TypeVar, Type, List

import httpx
from httpx import Response
from pydantic import BaseModel

from src.exception import RemoteServiceUnavailable

T = TypeVar('T', bound=BaseModel)


class HTTPClient:

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Инициализация HTTP клиента.
        
        Args:
            base_url: Базовый URL для всех запросов
            timeout: Таймаут в секундах (по умолчанию: 10)
        """
        self.base_url: str = base_url
        self.timeout: float = timeout

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Response:
        """
        Выполнение GET-запроса по указанному пути.
        
        Args:
            path: Путь, который будет добавлен к базовому URL
            params: Опциональные параметры запроса
            
        Returns:
            HTTP-ответ
            
        Raises:
            RemoteServiceUnavailable: Если произошла ошибка подключения к удаленному сервису
        """
        base = str(self.base_url).rstrip('/')
        normalized_path = '/' + path.lstrip('/')
        url: str = f"{base}{normalized_path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response: Response = await client.get(url, params=params)
                response.raise_for_status()
                return response
        except httpx.ConnectError as err:
            error_type: str = err.__class__.__name__
            msg: str = err.args[0]
            raise RemoteServiceUnavailable(error_type, msg) from err

    async def get_json(
        self, path: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выполнение GET-запроса и возврат JSON-ответа в виде словаря.
        
        Args:
            path: Путь, который будет добавлен к базовому URL
            params: Опциональные параметры запроса
            
        Returns:
            JSON-ответ в виде словаря
            
        Raises:
            RemoteServiceUnavailable: Если произошла ошибка подключения к удаленному сервису
        """
        response: Response = await self.get(path, params)
        return response.json()

    async def get_model(
        self,
        path: str,
        model_class: Type[T],
        params: Optional[Dict[str, Any]] = None
    ) -> T:
        """
        Выполнение GET-запроса и преобразование ответа в указанную модель.
        
        Args:
            path: Путь, который будет добавлен к базовому URL
            model_class: Класс Pydantic-модели для преобразования ответа
            params: Опциональные параметры запроса
            
        Returns:
            Экземпляр указанной модели
            
        Raises:
            RemoteServiceUnavailable: Если произошла ошибка подключения к удаленному сервису
        """
        data: Dict[str, Any] = await self.get_json(path, params)
        return model_class.model_validate(data)

    async def get_model_list(
        self, path: str,
        model_class: Type[T],
        params: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Выполнение GET-запроса и преобразование ответа в список моделей.
        
        Args:
            path: Путь, который будет добавлен к базовому URL
            model_class: Класс Pydantic-модели для преобразования каждого элемента
            params: Опциональные параметры запроса
            
        Returns:
            Список экземпляров указанной модели
            
        Raises:
            RemoteServiceUnavailable: Если произошла ошибка подключения к удаленному сервису
        """
        response: Response = await self.get(path, params)
        data: Any = response.json()

        if not isinstance(data, list):
            raise ValueError(f"Ожидался ответ в виде списка, но получен {type(data)}")

        return [model_class.model_validate(item) for item in data]
