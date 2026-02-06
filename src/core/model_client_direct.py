"""
Direct Model Client

Client that connects directly to provider APIs (Google, OpenAI, Anthropic, Ollama).
"""

import json
import logging
import uuid
from collections.abc import AsyncIterator, Sequence
from typing import Any

from src.core.model_client_base import BaseModelClient
from src.core.model_utils import (
    ChatResponse,
    ClientConfig,
    Message,
    Provider,
    StreamChunk,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class DirectModelClient(BaseModelClient):
    """Client that connects directly to provider APIs."""

    # Provider detection patterns
    PROVIDER_PATTERNS = {
        Provider.GOOGLE: ["gemini-", "palm-"],
        Provider.OPENAI: ["gpt-", "o1", "o3"],
        Provider.ANTHROPIC: ["claude-"],
        Provider.OLLAMA: [],
    }

    def __init__(self, config: ClientConfig):
        self.config = config
        self._providers: dict[Provider, Any] = {}

    async def __aenter__(self):
        """Context manager entry - ensure providers are connected."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure all providers are closed."""
        await self.close()
        return False

    async def connect(self) -> None:
        """Initialize provider clients."""
        # Google Gemini
        if self.config.google_api_key:
            try:
                from google import genai
                self._providers[Provider.GOOGLE] = genai.Client(
                    api_key=self.config.google_api_key
                )
                logger.info("Google Gemini client initialized")
            except ImportError:
                logger.warning("google-genai not installed")

        # OpenAI
        if self.config.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self._providers[Provider.OPENAI] = AsyncOpenAI(
                    api_key=self.config.openai_api_key
                )
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("openai not installed")

        # Anthropic
        if self.config.anthropic_api_key:
            try:
                from anthropic import AsyncAnthropic
                self._providers[Provider.ANTHROPIC] = AsyncAnthropic(
                    api_key=self.config.anthropic_api_key
                )
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("anthropic not installed")

        # Ollama (always available if running)
        try:
            import httpx
            self._providers[Provider.OLLAMA] = httpx.AsyncClient(
                base_url=self.config.ollama_base_url,
                timeout=120.0,
            )
            logger.info("Ollama client initialized")
        except Exception:
            pass

        if not self._providers:
            raise RuntimeError("No providers available. Check your API keys.")

    def _detect_provider(self, model: str) -> Provider:
        """Detect provider from model name."""
        for provider, patterns in self.PROVIDER_PATTERNS.items():
            for pattern in patterns:
                if model.startswith(pattern):
                    if provider in self._providers:
                        return provider
        # Default to first available
        if not self._providers:
            raise RuntimeError("No providers available. Check your API keys.")
        return next(iter(self._providers.keys()))

    async def chat(
        self,
        messages: Sequence[Message | dict],
        tools: Sequence[ToolDefinition | dict] | None = None,
        **kwargs,
    ) -> ChatResponse:
        if not self._providers:
            await self.connect()

        model = kwargs.get("model", self.config.model)
        provider = self._detect_provider(model)

        if provider == Provider.GOOGLE:
            return await self._chat_google(messages, tools, **kwargs)
        elif provider == Provider.OPENAI:
            return await self._chat_openai(messages, tools, **kwargs)
        elif provider == Provider.ANTHROPIC:
            return await self._chat_anthropic(messages, tools, **kwargs)
        else:
            return await self._chat_ollama(messages, tools, **kwargs)

    async def _chat_google(
        self,
        messages: Sequence[Message | dict],
        tools: Sequence[ToolDefinition | dict] | None = None,
        **kwargs,
    ) -> ChatResponse:
        """Chat with Google Gemini."""
        from google.genai import types

        client = self._providers[Provider.GOOGLE]
        model = kwargs.get("model", self.config.model)

        # Convert messages to Gemini format
        contents = []
        system_instruction = self.config.system_prompt

        for m in messages:
            msg = m if isinstance(m, dict) else m.to_dict()
            role = msg.get("role", "user")

            if role == "system":
                system_instruction = msg.get("content", "")
                continue

            gemini_role = "user" if role == "user" else "model"
            parts = []

            if msg.get("content"):
                parts.append(types.Part(text=msg["content"]))

            if msg.get("thought"):
                parts.append(types.Part(thought=msg["thought"]))

            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool arguments: {args_str}")
                        args = {}

                    fc_obj = types.FunctionCall(
                        name=func.get("name"),
                        args=args,
                    )

                    thought_sig = tc.get("thought_signature") or func.get("thought_signature")

                    parts.append(types.Part(
                        function_call=fc_obj,
                        thought_signature=thought_sig
                    ))

            if role == "tool" and msg.get("tool_call_id"):
                parts.append(types.Part(
                    function_response=types.FunctionResponse(
                        name=msg.get("name", "function"),
                        response={"result": msg.get("content", "")},
                    )
                ))

            if parts:
                contents.append(types.Content(role=gemini_role, parts=parts))

        # Build config
        gen_config_dict = {
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        if self.config.max_tokens:
            gen_config_dict["max_output_tokens"] = self.config.max_tokens

        if tools:
            function_declarations = []
            for t in tools:
                if isinstance(t, ToolDefinition):
                    function_declarations.append(t.to_genai_format())
                else:
                    func = t.get("function", t)
                    function_declarations.append(
                        types.FunctionDeclaration(
                            name=func.get("name"),
                            description=func.get("description", ""),
                            parameters=func.get("parameters", {}),
                        )
                    )
            gen_config_dict["tools"] = [types.Tool(function_declarations=function_declarations)]
            gen_config_dict["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(
                disable=True
            )

        if system_instruction:
            gen_config_dict["system_instruction"] = system_instruction

        gen_config = types.GenerateContentConfig(**gen_config_dict)

        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=gen_config,
        )

        # Extract response
        content = None
        tool_calls = None
        finish_reason = "stop"

        if not response.candidates:
            logger.warning("No candidates in Gemini response")
            return ChatResponse(
                content=None,
                tool_calls=None,
                finish_reason="error",
                usage=None,
                raw=response,
            )

        candidate = response.candidates[0]
        texts = []
        thoughts = []
        for part in candidate.content.parts:
            if hasattr(part, "text") and part.text:
                texts.append(part.text)
            elif hasattr(part, "thought") and part.thought:
                thoughts.append(part.thought)
            elif hasattr(part, "function_call") and part.function_call:
                if tool_calls is None:
                    tool_calls = []
                fc = part.function_call
                try:
                    args = dict(fc.args) if fc.args else {}
                except (TypeError, ValueError) as e:
                    from src.core.errors import DoraemonException, ErrorCategory
                    raise DoraemonException(
                        f"Invalid tool arguments: {fc.args}",
                        category=ErrorCategory.PERMANENT,
                        context={"tool": fc.name, "args": str(fc.args)}
                    ) from e
                tc_dict = {
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "type": "function",
                    "function": {
                        "name": fc.name,
                        "arguments": json.dumps(args),
                    },
                }
                if hasattr(part, "thought_signature") and part.thought_signature:
                    tc_dict["thought_signature"] = part.thought_signature
                elif isinstance(part, dict) and part.get("thought_signature"):
                    tc_dict["thought_signature"] = part.get("thought_signature")

                tool_calls.append(tc_dict)
        if texts:
            content = "".join(texts)

        thought = "".join(thoughts) if thoughts else None

        if tool_calls:
            finish_reason = "tool_calls"

        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                "completion_tokens": response.usage_metadata.candidates_token_count or 0,
                "total_tokens": response.usage_metadata.total_token_count or 0,
            }

        return ChatResponse(
            content=content,
            thought=thought,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            raw=response,
        )

    async def _chat_openai(
        self,
        messages: Sequence[Message | dict],
        tools: Sequence[ToolDefinition | dict] | None = None,
        **kwargs,
    ) -> ChatResponse:
        """Chat with OpenAI."""
        client = self._providers[Provider.OPENAI]
        model = kwargs.get("model", self.config.model)

        msg_list = []
        for m in messages:
            msg_list.append(m if isinstance(m, dict) else m.to_dict())

        params = {
            "model": model,
            "messages": msg_list,
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        if tools:
            params["tools"] = [
                t.to_openai_format() if isinstance(t, ToolDefinition) else t
                for t in tools
            ]

        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens

        response = await client.chat.completions.create(**params)

        if not response.choices:
            logger.warning("No choices in OpenAI response")
            return ChatResponse(
                content=None,
                tool_calls=None,
                finish_reason="error",
                usage=None,
                raw=response,
            )
        choice = response.choices[0]

        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in choice.message.tool_calls
            ]

        return ChatResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else None,
            raw=response,
        )

    async def _chat_anthropic(
        self,
        messages: Sequence[Message | dict],
        tools: Sequence[ToolDefinition | dict] | None = None,
        **kwargs,
    ) -> ChatResponse:
        """Chat with Anthropic Claude."""
        client = self._providers[Provider.ANTHROPIC]
        model = kwargs.get("model", self.config.model)

        system = self.config.system_prompt
        msg_list = []

        for m in messages:
            msg = m if isinstance(m, dict) else m.to_dict()
            role = msg.get("role", "user")

            if role == "system":
                system = msg.get("content", "")
                continue

            if role == "tool":
                msg_list.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id"),
                        "content": msg.get("content", ""),
                    }],
                })
            else:
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        args_str = func.get("arguments", "{}")
                        try:
                            args = json.loads(args_str) if isinstance(args_str, str) else args_str
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse tool arguments: {args_str}")
                            args = {}
                        content.append({
                            "type": "tool_use",
                            "id": tc.get("id"),
                            "name": func.get("name"),
                            "input": args,
                        })
                msg_list.append({
                    "role": "assistant" if role == "assistant" else "user",
                    "content": content or msg.get("content"),
                })

        params = {
            "model": model,
            "messages": msg_list,
            "max_tokens": self.config.max_tokens or 4096,
        }

        if system:
            params["system"] = system

        if tools:
            params["tools"] = [
                {
                    "name": t.name if isinstance(t, ToolDefinition) else t["function"]["name"],
                    "description": t.description if isinstance(t, ToolDefinition) else t["function"].get("description", ""),
                    "input_schema": t.parameters if isinstance(t, ToolDefinition) else t["function"].get("parameters", {}),
                }
                for t in tools
            ]

        response = await client.messages.create(**params)

        content = None
        tool_calls = None

        for block in response.content:
            if block.type == "text":
                content = (content or "") + block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })

        return ChatResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop",
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            raw=response,
        )

    async def _chat_ollama(
        self,
        messages: Sequence[Message | dict],
        tools: Sequence[ToolDefinition | dict] | None = None,
        **kwargs,
    ) -> ChatResponse:
        """Chat with Ollama."""
        client = self._providers[Provider.OLLAMA]
        model = kwargs.get("model", self.config.model)

        msg_list = []
        for m in messages:
            msg = m if isinstance(m, dict) else m.to_dict()
            msg_list.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        payload = {
            "model": model,
            "messages": msg_list,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
            },
        }

        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            content=data.get("message", {}).get("content"),
            tool_calls=None,
            finish_reason="stop",
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            },
            raw=data,
        )

    async def chat_stream(
        self,
        messages: Sequence[Message | dict],
        tools: Sequence[ToolDefinition | dict] | None = None,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Streaming chat - currently falls back to non-streaming for direct mode."""
        response = await self.chat(messages, tools, **kwargs)
        if False:
            yield StreamChunk()  # Ensure it's an async generator
        yield StreamChunk(
            content=response.content,
            tool_calls=response.tool_calls,
            finish_reason=response.finish_reason,
            usage=response.usage,
        )

    async def list_models(self) -> list[dict]:
        """List available models from all providers."""
        models = []

        if Provider.GOOGLE in self._providers:
            models.extend([
                {"id": "gemini-2.5-flash-preview", "provider": "google"},
                {"id": "gemini-2.5-pro-preview", "provider": "google"},
            ])

        if Provider.OPENAI in self._providers:
            models.extend([
                {"id": "gpt-4o", "provider": "openai"},
                {"id": "gpt-4o-mini", "provider": "openai"},
            ])

        if Provider.ANTHROPIC in self._providers:
            models.extend([
                {"id": "claude-sonnet-4-20250514", "provider": "anthropic"},
                {"id": "claude-3-5-haiku-20241022", "provider": "anthropic"},
            ])

        return models

    async def close(self) -> None:
        """Close all provider clients."""
        for provider, client in self._providers.items():
            if provider == Provider.OLLAMA and hasattr(client, "aclose"):
                await client.aclose()
        self._providers.clear()
