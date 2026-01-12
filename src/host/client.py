import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google.generativeai.types import FunctionDeclaration

@dataclass
class TraceEvent:
    type: str  # "tool_call", "tool_result", "model_think", "user_input"
    name: str  # tool name or event name
    data: Any
    timestamp: float
    duration_ms: Optional[float] = None

class TraceLogger:
    def __init__(self):
        self.events: List[TraceEvent] = []

    def log(self, type: str, name: str, data: Any, duration_ms: float = 0):
        event = TraceEvent(
            type=type,
            name=name,
            data=data,
            timestamp=time.time(),
            duration_ms=duration_ms
        )
        self.events.append(event)

    def export(self) -> List[Dict]:
        return [asdict(e) for e in self.events]

class MultiServerMCPClient:
    def __init__(self, tracer: Optional[TraceLogger] = None):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map: Dict[str, str] = {} 
        self.tracer = tracer or TraceLogger() # Default no-op logger if None

    async def connect_to_config(self, config: Dict[str, Any]):
        """根据 config.json 连接所有定义的 servers"""
        servers_conf = config.get("mcpServers", {})
        
        # 解析包根路径
        pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        for name, details in servers_conf.items():
            command = details.get("command")
            args = details.get("args", [])
            env = os.environ.copy()
            env.update(details.get("env", {}))
            
            # 智能路径解析
            resolved_args = []
            for arg in args:
                if arg.endswith(".py"):
                    # 1. 绝对路径
                    if os.path.isabs(arg):
                        resolved_args.append(arg)
                        continue
                    
                    # 2. 内置 Server (pkg_root + arg)
                    # 假设 config 写 "src/servers/xxx.py"
                    clean_arg = arg.replace("src/", "") if arg.startswith("src/") else arg
                    pkg_path = os.path.join(pkg_root, clean_arg)
                    
                    # 简单的启发式：尝试多种组合
                    candidates = [
                        arg,
                        os.path.abspath(arg),
                        pkg_path,
                        os.path.join(pkg_root, "servers", os.path.basename(arg))
                    ]
                    
                    final_path = arg
                    for p in candidates:
                        if os.path.exists(p):
                            final_path = p
                            break
                    resolved_args.append(final_path)
                else:
                    resolved_args.append(arg)

            params = StdioServerParameters(command=command, args=resolved_args, env=env)
            
            try:
                read, write = await self.exit_stack.enter_async_context(stdio_client(params))
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                self.sessions[name] = session
                
                tools_list = await session.list_tools()
                for tool in tools_list.tools:
                    self.tool_map[tool.name] = name
                    
            except Exception as e:
                print(f"[Error] Failed to connect to {name}: {e}")

    async def get_genai_tools(self) -> List[Any]:
        """将 MCP 工具定义转换为 Google GenAI 的 FunctionDeclaration"""
        genai_tools = []
        
        for name, session in self.sessions.items():
            result = await session.list_tools()
            for tool in result.tools:
                # 兼容性处理：OpenAI/Gemini 的 Schema 转换
                func_decl = FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=tool.inputSchema
                )
                genai_tools.append(func_decl)
                
        return genai_tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """路由工具调用并记录 Trace"""
        start_time = time.time()
        
        try:
            server_name = self.tool_map.get(tool_name)
            if not server_name:
                raise ValueError(f"Tool {tool_name} not found.")
                
            session = self.sessions[server_name]
            
            # Log Request
            self.tracer.log("tool_call", tool_name, arguments)
            
            result = await session.call_tool(tool_name, arguments)
            
            # Extract content
            content = "No content"
            if result.content and len(result.content) > 0:
                content = result.content[0].text
                
            duration = (time.time() - start_time) * 1000
            self.tracer.log("tool_result", tool_name, content, duration)
            
            return content
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.tracer.log("tool_error", tool_name, str(e), duration)
            raise e

    async def cleanup(self):
        await self.exit_stack.aclose()