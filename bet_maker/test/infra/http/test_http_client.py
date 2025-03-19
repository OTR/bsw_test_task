import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import httpx
from httpx import Response

from src.infra.http.http_client import HTTPClient
from src.domain.entity import Event
from src.domain.vo import EventStatus
from src.exception import RemoteServiceUnavailable

pytestmark = pytest.mark.asyncio


class TestHTTPClient:
    @pytest.fixture
    def http_client(self):
        return HTTPClient(base_url="https://api.example.com")

    @pytest.fixture
    def mock_response(self):
        response = MagicMock(spec=Response)
        response.status_code = 200
        response.raise_for_status = MagicMock()
        return response

    @pytest.fixture
    def sample_event_data(self):
        return {
            "event_id": 1,
            "title": "Test Event",
            "coefficient": "1.50",
            "deadline": int(datetime.now().timestamp()) + 3600,
            "status": "NEW"
        }

    async def test_get_success(self, http_client, mock_response):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            response = await http_client.get("/test")
            
            assert response is mock_response
            mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
                "https://api.example.com/test", params=None
            )

    async def test_get_connection_error(self, http_client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = \
                httpx.ConnectError("Connection refused")
            
            with pytest.raises(RemoteServiceUnavailable) as exc_info:
                await http_client.get("/test")
            
            assert "ConnectError" in str(exc_info.value)
            assert "Connection refused" in str(exc_info.value)

    async def test_get_json(self, http_client, mock_response):
        expected_data = {"key": "value"}
        mock_response.json.return_value = expected_data
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            data = await http_client.get_json("/test")
            
            assert data == expected_data
            mock_response.json.assert_called_once()

    async def test_get_model(self, http_client, mock_response, sample_event_data):
        mock_response.json.return_value = sample_event_data
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            event = await http_client.get_model("/event/1", Event)
            
            assert isinstance(event, Event)
            assert event.event_id == 1
            assert event.status == EventStatus.NEW

    async def test_get_model_list(self, http_client, mock_response, sample_event_data):
        mock_response.json.return_value = [sample_event_data, sample_event_data]
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            events = await http_client.get_model_list("/events", Event)
            
            assert isinstance(events, list)
            assert len(events) == 2
            assert all(isinstance(event, Event) for event in events)
            assert all(event.event_id == 1 for event in events)

    async def test_get_model_list_invalid_response(self, http_client, mock_response):
        mock_response.json.return_value = {"key": "value"}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(ValueError) as exc_info:
                await http_client.get_model_list("/events", Event)
            
            assert "Ожидался ответ в виде списка, но получен <class 'dict'>" in str(exc_info.value)
