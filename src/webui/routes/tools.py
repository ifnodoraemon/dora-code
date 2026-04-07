"""
Tools API Routes

Lists available tools.
"""

from fastapi import APIRouter

from src.runtime.bootstrap import get_tool_catalog

router = APIRouter()


@router.get("/")
async def list_tools(mode: str = "build"):
    """List available tools for a mode."""
    tools = await get_tool_catalog(mode=mode)
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "policy": tool["policy"],
            }
            for tool in tools
        ]
    }
