"""
Unit tests for model_client.py

Tests the unified model client interface, retry logic, and error handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.errors import ConfigurationError, RateLimitError, TransientError
from src.core.model_client import (
    ChatResponse,
    ClientConfig,
    ClientMode,
    DirectModelClient,
    GatewayModelClient,
    Message,
    ModelClient,
)


class TestGatewayModelClient:
    """Tests for GatewayModelClient."""

    @pytest.mark.asyncio
    async def test_context_manager_connects_and_closes(self):
        """Test that context manager properly connects and closes client."""
        config = ClientConfig(
            mode=ClientMode.GATEWAY,
            gateway_url="http://test.com",
            model="test-model",
        )
        client = GatewayModelClient(config)

        # Mock the HTTP client
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            async with client:
                # Should have connected
                assert client._client is not None

            # Should have closed
            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self):
        """Test that client retries on rate limit with backoff."""
        config = ClientConfig(
            mode=ClientMode.GATEWAY,
            gateway_url="http://test.com",
            model="test-model",
        )
        client = GatewayModelClient(config)

        # Mock HTTP client
        mock_client = AsyncMock()
        client._client = mock_client

        # First call returns 429, second succeeds
        from httpx import Response, HTTPStatusError, Request

        rate_limit_response = Response(
            status_code=429,
            headers={"Retry-After": "1"},
            request=Request("POST", "http://test.com/v1/chat/completions"),
        )
        success_response = Response(
            status_code=200,
            json={"choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}]},
            request=Request("POST", "http://test.com/v1/chat/completions"),
        )

        mock_client.post.side_effect = [
            HTTPStatusError("Rate limited", request=rate_limit_response.request, response=rate_limit_response),
            success_response,
        ]

        # Mock response.json()
        success_response.json = lambda: {
            "choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}]
        }

        messages = [Message(role="user", content="Test")]

        # Should retry and succeed
        with patch("asyncio.sleep"):  # Speed up test by mocking sleep
            response = await client.chat(messages)

        assert response.content == "Success"
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self):
        """Test that client retries on 5xx server errors."""
        config = ClientConfig(
            mode=ClientMode.GATEWAY,
            gateway_url="http://test.com",
            model="test-model",
        )
        client = GatewayModelClient(config)

        mock_client = AsyncMock()
        client._client = mock_client

        from httpx import Response, HTTPStatusError, Request

        server_error_response = Response(
            status_code=503,
            request=Request("POST", "http://test.com/v1/chat/completions"),
        )
        success_response = Response(
            status_code=200,
            json={"choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}]},
            request=Request("POST", "http://test.com/v1/chat/completions"),
        )

        mock_client.post.side_effect = [
            HTTPStatusError("Server error", request=server_error_response.request, response=server_error_response),
            success_response,
        ]

        success_response.json = lambda: {
            "choices": [{"message": {"content": "Success"}, "finish_reason": "stop"}]
        }

        messages = [Message(role="user", content="Test")]

        with patch("asyncio.sleep"):
            response = await client.chat(messages)

        assert response.content == "Success"
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self):
        """Test that client does NOT retry on 4xx client errors."""
        config = ClientConfig(
            mode=ClientMode.GATEWAY,
            gateway_url="http://test.com",
            model="test-model",
        )
        client = GatewayModelClient(config)

        mock_client = AsyncMock()
        client._client = mock_client

        from httpx import Response, HTTPStatusError, Request
        from src.core.errors import DoraemonException

        client_error_response = Response(
            status_code=400,
            text="Bad request",
            request=Request("POST", "http://test.com/v1/chat/completions"),
        )

        mock_client.post.side_effect = HTTPStatusError(
            "Bad request",
            request=client_error_response.request,
            response=client_error_response
        )

        messages = [Message(role="user", content="Test")]

        # Should raise DoraemonException without retry
        with pytest.raises(DoraemonException):
            await client.chat(messages)

        # Should only call once (no retry)
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_raises_config_error_if_client_fails_to_initialize(self):
        """Test that ConfigurationError is raised if client initialization fails."""
        config = ClientConfig(
            mode=ClientMode.GATEWAY,
            gateway_url="http://test.com",
            model="test-model",
        )
        client = GatewayModelClient(config)

        # Force client to remain None
        with patch.object(client, "connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = None
            client._client = None

            messages = [Message(role="user", content="Test")]

            with pytest.raises(ConfigurationError, match="Failed to initialize HTTP client"):
                await client.chat(messages)


class TestDirectModelClient:
    """Tests for DirectModelClient."""

    @pytest.mark.asyncio
    async def test_context_manager_connects_and_closes(self):
        """Test that context manager properly connects and closes providers."""
        config = ClientConfig(
            mode=ClientMode.DIRECT,
            google_api_key="test-key",
            model="gemini-test",
        )
        client = DirectModelClient(config)

        with patch("google.genai.Client") as mock_genai:
            mock_genai.return_value = MagicMock()

            async with client:
                # Should have connected
                assert len(client._providers) > 0

            # Should have cleared providers
            assert len(client._providers) == 0

    @pytest.mark.asyncio
    async def test_raises_error_if_no_providers_available(self):
        """Test that error is raised if no providers are configured."""
        config = ClientConfig(
            mode=ClientMode.DIRECT,
            model="test-model",
        )
        client = DirectModelClient(config)

        # Mock httpx to fail so Ollama also fails
        with patch("httpx.AsyncClient", side_effect=Exception("No httpx")):
            with pytest.raises(RuntimeError, match="No providers available"):
                await client.connect()


class TestModelClient:
    """Tests for ModelClient factory."""

    @pytest.mark.asyncio
    async def test_create_gateway_client(self):
        """Test creating a gateway mode client."""
        config = ClientConfig(
            mode=ClientMode.GATEWAY,
            gateway_url="http://test.com",
            model="test-model",
        )

        with patch("httpx.AsyncClient"):
            client = await ModelClient.create(config)
            assert isinstance(client, GatewayModelClient)

    @pytest.mark.asyncio
    async def test_create_direct_client(self):
        """Test creating a direct mode client."""
        config = ClientConfig(
            mode=ClientMode.DIRECT,
            google_api_key="test-key",
            model="gemini-test",
        )

        with patch("google.genai.Client"):
            client = await ModelClient.create(config)
            assert isinstance(client, DirectModelClient)

    def test_get_mode_detects_gateway(self):
        """Test that get_mode detects gateway mode from environment."""
        with patch.dict("os.environ", {"DORAEMON_GATEWAY_URL": "http://test.com"}):
            mode = ModelClient.get_mode()
            assert mode == ClientMode.GATEWAY

    def test_get_mode_detects_direct(self):
        """Test that get_mode detects direct mode when no gateway URL."""
        with patch.dict("os.environ", {}, clear=True):
            mode = ModelClient.get_mode()
            assert mode == ClientMode.DIRECT


class TestMessage:
    """Tests for Message class."""

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all non-None fields."""
        msg = Message(
            role="assistant",
            content="Hello",
            thought="Thinking...",
            tool_calls=[{"id": "1", "name": "test"}],
        )
        d = msg.to_dict()

        assert d["role"] == "assistant"
        assert d["content"] == "Hello"
        assert d["thought"] == "Thinking..."
        assert d["tool_calls"] == [{"id": "1", "name": "test"}]

    def test_to_dict_excludes_none_fields(self):
        """Test that to_dict excludes None fields."""
        msg = Message(role="user", content="Hello")
        d = msg.to_dict()

        assert "role" in d
        assert "content" in d
        assert "thought" not in d
        assert "tool_calls" not in d


class TestChatResponse:
    """Tests for ChatResponse class."""

    def test_has_tool_calls_true(self):
        """Test has_tool_calls returns True when tool calls present."""
        response = ChatResponse(
            content=None,
            tool_calls=[{"id": "1", "name": "test"}],
        )
        assert response.has_tool_calls is True

    def test_has_tool_calls_false(self):
        """Test has_tool_calls returns False when no tool calls."""
        response = ChatResponse(content="Hello")
        assert response.has_tool_calls is False
