"""Tests for tool_selector.py"""
import pytest
from src.core.tool_selector import ToolSelector

class TestToolSelector:
    def test_initialization(self):
        selector = ToolSelector()
        assert selector is not None

    def test_get_tools_for_plan_mode(self):
        selector = ToolSelector()
        tools = selector.get_tools_for_mode("plan")
        assert isinstance(tools, list)

    def test_get_tools_for_build_mode(self):
        selector = ToolSelector()
        tools = selector.get_tools_for_mode("build")
        assert isinstance(tools, list)

    def test_plan_mode_has_fewer_tools(self):
        selector = ToolSelector()
        plan_tools = selector.get_tools_for_mode("plan")
        build_tools = selector.get_tools_for_mode("build")
        assert len(plan_tools) <= len(build_tools)
