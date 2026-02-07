"""
Unified Model Client

Provides a unified interface for both Gateway and Direct modes.

Modes:
1. Gateway Mode: Connect to a Model Gateway server
   - Only needs: DORAEMON_GATEWAY_URL + DORAEMON_API_KEY
   - Supports all providers through the gateway

2. Direct Mode: Connect directly to provider APIs
   - Needs individual API keys: GOOGLE_API_KEY, OPENAI_API_KEY, etc.
   - Supports provider-specific features

Usage:
    # Auto-detect mode based on environment
    client = await ModelClient.create()

    # Chat
    response = await client.chat(messages, tools)

    # Stream
    async for chunk in client.chat_stream(messages, tools):
        print(chunk.content)
"""

import os

# Re-export base class
from src.core.model_client_base import BaseModelClient
from src.core.model_client_direct import DirectModelClient

# Re-export client implementations
from src.core.model_client_gateway import GatewayModelClient

# Re-export all types from model_utils for backward compatibility
from src.core.model_utils import (
    ChatResponse,
    ClientConfig,
    ClientMode,
    Message,
    Provider,
    StreamChunk,
    ToolCall,
    ToolDefinition,
)

__all__ = [
    # Types
    "Message",
    "ToolDefinition",
    "ChatResponse",
    "StreamChunk",
    "ToolCall",
    "ClientConfig",
    "ClientMode",
    "Provider",
    # Clients
    "BaseModelClient",
    "GatewayModelClient",
    "DirectModelClient",
    "ModelClient",
]


class ModelClient:
    """
    Unified model client factory.

    Auto-detects mode based on environment configuration.
    """

    @staticmethod
    async def create(config: ClientConfig | None = None) -> BaseModelClient:
        """
        Create a model client based on configuration.

        Args:
            config: Optional configuration. If not provided, loads from environment.

        Returns:
            Configured model client (Gateway or Direct mode)
        """
        if config is None:
            config = ClientConfig.from_env()

        if config.mode == ClientMode.GATEWAY:
            client: BaseModelClient = GatewayModelClient(config)
        else:
            client = DirectModelClient(config)

        await client.connect()
        return client

    @staticmethod
    def get_mode() -> ClientMode:
        """Get current mode based on environment."""
        if os.getenv("DORAEMON_GATEWAY_URL"):
            return ClientMode.GATEWAY
        return ClientMode.DIRECT

    @staticmethod
    def get_mode_info() -> dict:
        """Get information about current mode configuration."""
        mode = ModelClient.get_mode()

        if mode == ClientMode.GATEWAY:
            return {
                "mode": "gateway",
                "gateway_url": os.getenv("DORAEMON_GATEWAY_URL"),
                "has_key": bool(os.getenv("DORAEMON_API_KEY")),
            }
        else:
            return {
                "mode": "direct",
                "providers": {
                    "google": bool(os.getenv("GOOGLE_API_KEY")),
                    "openai": bool(os.getenv("OPENAI_API_KEY")),
                    "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
                    "ollama": True,
                },
            }
