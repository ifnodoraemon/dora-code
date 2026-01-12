import os
import asyncio
from contextlib import AsyncExitStack
from typing import Dict, Any, List, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google.generativeai.types import FunctionDeclaration, Tool

class MultiServerMCPClient:
    """
    一个聚合器，负责管理与多个 MCP Server 的连接。
    它将多个 Server 的工具合并，暴露给 LLM。
    """
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map: Dict[str, str] = {} # tool_name -> server_name

    async def connect_to_config(self, config: Dict[str, Any]):
        """根据 config.json 连接所有定义的 servers"""
        servers_conf = config.get("mcpServers", {})
        
        for name, details in servers_conf.items():
            command = details.get("command")
            args = details.get("args", [])
            env = os.environ.copy()
            env.update(details.get("env", {}))
            
            # 转换相对路径
            cwd = os.getcwd()
            args = [os.path.join(cwd, arg) if arg.endswith(".py") and not arg.startswith("/") else arg for arg in args]

            params = StdioServerParameters(command=command, args=args, env=env)
            
            try:
                # 使用 exit_stack 管理多个上下文
                read, write = await self.exit_stack.enter_async_context(stdio_client(params))
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                self.sessions[name] = session
                print(f"[System] Connected to MCP Server: {name}")
                
                # 注册该 Server 的工具
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
                # 简单的 Schema 转换
                # 注意：这里是简化的，Gemini 和 MCP 的 JSON Schema 略有不同，但通常兼容
                func_decl = FunctionDeclaration(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=tool.inputSchema
                )
                genai_tools.append(func_decl)
                
        return genai_tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """路由工具调用到对应的 Server"""
        server_name = self.tool_map.get(tool_name)
        if not server_name:
            raise ValueError(f"Tool {tool_name} not found in any connected server.")
            
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        
        # 提取结果文本
        if result.content and len(result.content) > 0:
            return result.content[0].text
        return "Tool executed successfully but returned no content."

    async def cleanup(self):
        await self.exit_stack.aclose()
