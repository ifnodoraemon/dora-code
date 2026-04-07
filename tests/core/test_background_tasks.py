import asyncio

import pytest

from src.core.background_tasks import BackgroundTaskManager, TaskStatus
from src.host.tools import ToolRegistry


@pytest.mark.asyncio
async def test_start_tool_task_blocks_background_unsafe_tools():
    manager = BackgroundTaskManager()
    registry = ToolRegistry()

    def ask_user(question: str) -> str:
        return question

    registry.register(ask_user, name="ask_user", metadata={"capability_group": "read"})

    with pytest.raises(RuntimeError, match="background task"):
        await manager.start_tool_task(
            name="Interactive prompt",
            description="Should not be allowed in background",
            coroutine=asyncio.sleep(0),
            tool_names=["ask_user"],
            tool_registry=registry,
        )


@pytest.mark.asyncio
async def test_start_tool_task_allows_background_safe_tools():
    manager = BackgroundTaskManager()
    registry = ToolRegistry()

    def read(path: str) -> str:
        return path

    registry.register(read, name="read", metadata={"capability_group": "read"})

    task_id = await manager.start_tool_task(
        name="Read files",
        description="Background-safe read task",
        coroutine=asyncio.sleep(0, result="done"),
        tool_names=["read"],
        tool_registry=registry,
    )

    await asyncio.sleep(0.05)
    task = manager.get_task(task_id)
    assert task is not None
    assert task.tool_names == ["read"]
    assert task.status == TaskStatus.COMPLETED
