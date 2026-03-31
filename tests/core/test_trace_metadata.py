from src.core.home import Trace


def test_trace_start_turn_includes_metadata():
    trace = Trace("session_test")
    trace.start_turn(
        "Plan the task",
        metadata={
            "mode": "plan",
            "capability_groups": ["read", "memory", "research", "task"],
            "active_tools": ["read", "search", "ask_user", "memory_get"],
            "active_skills": [],
            "active_mcp_extensions": [],
        },
    )

    event = trace.events[0]
    assert event.type == "turn_start"
    assert event.data["mode"] == "plan"
    assert event.data["capability_groups"] == ["read", "memory", "research", "task"]
    assert "memory_get" in event.data["active_tools"]
    assert event.data["active_skills"] == []
    assert event.data["active_mcp_extensions"] == []


def test_trace_tool_call_includes_source_metadata():
    trace = Trace("session_test")
    trace.start_turn("Use remote MCP tool")
    trace.tool_call(
        "docs_lookup",
        {"query": "mcp"},
        "result text",
        0.12,
        source="mcp_remote",
        metadata={
            "mcp_server": "docs",
            "mcp_transport": "streamable_http",
        },
    )

    event = trace.events[1]
    assert event.type == "tool_call"
    assert event.data["tool_source"] == "mcp_remote"
    assert event.data["mcp_server"] == "docs"
    assert event.data["mcp_transport"] == "streamable_http"
