from typing import Any, Dict, Optional, TypeVar, Type, List
from pydantic import BaseModel

import httpx
from httpx import Response

from src.exception import RemoteServiceUnavailable

T = TypeVar('T', bound=BaseModel)

class HTTPClient:

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Initialize the HTTP client with a base URL and optional timeout.
        
        Args:
            base_url: The base URL for all requests made by this client
            timeout: Request timeout in seconds (default: 10.0)
        """
        self.base_url: str = base_url
        self.timeout: float = timeout
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Response:
        """
        Make a GET request to the specified path.
        
        Args:
            path: The path to append to the base URL
            params: Optional query parameters
            
        Returns:
            The HTTP response
            
        Raises:
            RemoteServiceUnavailable: If there's a connection error to the remote service
        """
        # Convert base_url to string and ensure proper path construction
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

    async def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request and return the JSON response as a dictionary.
        
        Args:
            path: The path to append to the base URL
            params: Optional query parameters
            
        Returns:
            The JSON response as a dictionary
            
        Raises:
            RemoteServiceUnavailable: If there's a connection error to the remote service
        """
        response: Response = await self.get(path, params)
        return response.json()
    
    async def get_model(self, path: str, model_class: Type[T], params: Optional[Dict[str, Any]] = None) -> T:
        """
        Make a GET request and parse the response into the specified model.
        
        Args:
            path: The path to append to the base URL
            model_class: The Pydantic model class to parse the response into
            params: Optional query parameters
            
        Returns:
            An instance of the specified model
            
        Raises:
            RemoteServiceUnavailable: If there's a connection error to the remote service
        """
        data: Dict[str, Any] = await self.get_json(path, params)
        return model_class.model_validate(data)

    async def get_model_list(
        self, path: str,
        model_class: Type[T],
        params: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """
        Make a GET request and parse the response into a list of the specified model.
        
        Args:
            path: The path to append to the base URL
            model_class: The Pydantic model class to parse each item into
            params: Optional query parameters
            
        Returns:
            A list of instances of the specified model
            
        Raises:
            RemoteServiceUnavailable: If there's a connection error to the remote service
        """
        response: Response = await self.get(path, params)
        data: Any = response.json()
        
        if not isinstance(data, list):
            raise ValueError(f"Expected list response but got {type(data)}")
            
        return [model_class.model_validate(item) for item in data]
