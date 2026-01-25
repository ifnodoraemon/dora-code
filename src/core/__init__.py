"""Core utilities for Polymath."""

from .config import load_config
from .logger import setup_logger
from .checkpoint import CheckpointManager, CheckpointConfig
from .background_tasks import BackgroundTaskManager, get_task_manager, TaskStatus
from .subagents import SubagentManager, SubagentConfig, BUILTIN_AGENTS
from .hooks import HookManager, HookEvent, HookResult
from .session import SessionManager, SessionData
from .cost_tracker import CostTracker, BudgetConfig
from .command_history import CommandHistory, BashModeExecutor
from .plugins import PluginManager, PluginScope
from .workspace import WorkspaceManager
from .model_manager import ModelManager, ModelCapability, AVAILABLE_MODELS
from .model_client import (
    ModelClient,
    ClientMode,
    ClientConfig,
    ChatResponse,
    Message,
    ToolDefinition,
)
from .browser import BrowserManager, get_browser_manager
from .input_mode import InputManager, InputMode
from .thinking import ThinkingManager, ThinkingMode
from .doctor import Doctor
from .themes import ThemeManager, Theme, BUILTIN_THEMES
from .streaming import StreamManager, StreamingChat
from .parallel_executor import ParallelExecutor, ExecutionStrategy, ToolCall
from .mcp_client import MCPClient, MCPServerConfig
from .cache import ToolCache, get_tool_cache
from .file_watcher import FileWatcher, get_file_watcher
from .hot_reload import HotReloadManager, get_hot_reload_manager
from .permissions import PermissionManager, PermissionLevel, PermissionRule
from .tool_history import ToolHistoryManager, get_tool_history
from .task_recovery import TaskRecoveryManager, get_recovery_manager, TaskState
from .proxy import ProxyManager, ProxyConfig, get_proxy_manager
from .notifications import NotificationManager, get_notification_manager, notify
from .i18n import I18n, get_i18n, t
from .git_hooks import GitHooksManager, get_git_hooks_manager, GitHookType
from .log_rotation import LogRotationManager, RotationConfig, setup_rotating_logger
from .memory_layers import LayeredMemory, MemoryLayer, get_layered_memory

__all__ = [
    "load_config",
    "setup_logger",
    # Checkpoint
    "CheckpointManager",
    "CheckpointConfig",
    # Background Tasks
    "BackgroundTaskManager",
    "get_task_manager",
    "TaskStatus",
    # Subagents
    "SubagentManager",
    "SubagentConfig",
    "BUILTIN_AGENTS",
    # Hooks
    "HookManager",
    "HookEvent",
    "HookResult",
    # Session
    "SessionManager",
    "SessionData",
    # Cost Tracking
    "CostTracker",
    "BudgetConfig",
    # Command History
    "CommandHistory",
    "BashModeExecutor",
    # Plugins
    "PluginManager",
    "PluginScope",
    # Workspace
    "WorkspaceManager",
    # Model Manager
    "ModelManager",
    "ModelCapability",
    "AVAILABLE_MODELS",
    # Model Client (Unified API)
    "ModelClient",
    "ClientMode",
    "ClientConfig",
    "ChatResponse",
    "Message",
    "ToolDefinition",
    # Browser
    "BrowserManager",
    "get_browser_manager",
    # Input Mode
    "InputManager",
    "InputMode",
    # Thinking
    "ThinkingManager",
    "ThinkingMode",
    # Doctor
    "Doctor",
    # Themes
    "ThemeManager",
    "Theme",
    "BUILTIN_THEMES",
    # Streaming
    "StreamManager",
    "StreamingChat",
    # Parallel Executor
    "ParallelExecutor",
    "ExecutionStrategy",
    "ToolCall",
    # MCP Client
    "MCPClient",
    "MCPServerConfig",
    # Cache
    "ToolCache",
    "get_tool_cache",
    # File Watcher
    "FileWatcher",
    "get_file_watcher",
    # Hot Reload
    "HotReloadManager",
    "get_hot_reload_manager",
    # Permissions
    "PermissionManager",
    "PermissionLevel",
    "PermissionRule",
    # Tool History
    "ToolHistoryManager",
    "get_tool_history",
    # Task Recovery
    "TaskRecoveryManager",
    "get_recovery_manager",
    "TaskState",
    # Proxy
    "ProxyManager",
    "ProxyConfig",
    "get_proxy_manager",
    # Notifications
    "NotificationManager",
    "get_notification_manager",
    "notify",
    # I18n
    "I18n",
    "get_i18n",
    "t",
    # Git Hooks
    "GitHooksManager",
    "get_git_hooks_manager",
    "GitHookType",
    # Log Rotation
    "LogRotationManager",
    "RotationConfig",
    "setup_rotating_logger",
    # Memory Layers
    "LayeredMemory",
    "MemoryLayer",
    "get_layered_memory",
]
