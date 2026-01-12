import os
import asyncio
import json
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

# Google GenAI
import google.generativeai as genai
from google.generativeai.types import Tool as GenAITool

# 导入通用 MCP 客户端
from src.host.client import MultiServerMCPClient

app = typer.Typer()
console = Console()

# 加载 .env 环境变量
load_dotenv()

def load_config():
    """
    Cascading config loading:
    1. Project specific: ./.polymath/config.json
    2. User global: ~/.polymath/config.json
    3. Package default: (Installed dir)/.polymath/config.json
    """
    # 1. Project Level
    cwd_config = os.path.join(os.getcwd(), ".polymath", "config.json")
    if os.path.exists(cwd_config):
        return json.load(open(cwd_config, "r"))
    
    # 2. User Level
    home_config = os.path.expanduser("~/.polymath/config.json")
    if os.path.exists(home_config):
        return json.load(open(home_config, "r"))

    # 3. Package Default (Fallback)
    # 获取 src/host/cli.py 的位置 -> src/host -> src -> polymath root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pkg_config = os.path.join(base_dir, ".polymath", "config.json")
    
    if os.path.exists(pkg_config):
        return json.load(open(pkg_config, "r"))
        
    # Final Fallback
    return {"mcpServers": {}}

async def run_task_for_eval(task: str, project: str = "eval_test") -> str:
    """专为 Eval 设计的非交互式运行函数"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key: return "Error: No API Key"
    genai.configure(api_key=api_key)

    config = load_config()
    mcp_client = MultiServerMCPClient()
    await mcp_client.connect_to_config(config)

    try:
        active_tools = []
        for name, session in mcp_client.sessions.items():
            result = await session.list_tools()
            for tool in result.tools:
                tool_decl = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                active_tools.append(tool_decl)

        persona = config.get("persona", {})
        sys_prompt = f"You are {persona.get('name', 'Polymath')}. Answer the user request."
        
        model = genai.GenerativeModel("gemini-1.5-pro", tools=[genai.protos.Tool(function_declarations=active_tools)])
        chat = model.start_chat(enable_automatic_function_calling=False)

        # 发送任务
        response = chat.send_message(task)
        
        # 简单的单轮工具调用循环 (Eval 模式通常不需要太深的多轮)
        # 这里限制最大 5 次工具调用，防止死循环
        for _ in range(5):
            part = response.candidates[0].content.parts[0]
            if part.function_call:
                fc = part.function_call
                # Eval 模式下，自动批准所有操作 (Auto-Approve)
                # 注意：这在沙箱外运行非常危险，但在受控 Eval 环境是必须的
                try:
                    tool_result = await mcp_client.call_tool(fc.name, dict(fc.args))
                    response = chat.send_message(
                        genai.protos.Content(
                            parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fc.name,
                                    response={"result": tool_result}
                                )
                            )]
                        )
                    )
                except Exception as e:
                    return f"Tool Error: {e}"
            else:
                return response.text
                
        return "Error: Tool loop exceeded limit."

    finally:
        await mcp_client.cleanup()

async def chat_loop(project: str = "default"):
    # 1. 环境检查
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print("[red]错误: 未设置 GOOGLE_API_KEY[/red]")
        return
    genai.configure(api_key=api_key)

    console.print(f"[bold yellow]Project: {project}[/bold yellow]")

    # 2. 初始化 MCP 客户端
    config = load_config()
    mcp_client = MultiServerMCPClient()
    await mcp_client.connect_to_config(config)

    # 敏感工具列表
    SENSITIVE_TOOLS = ["execute_python", "write_file", "save_note"]

    try:
        active_tools = []
        for name, session in mcp_client.sessions.items():
            result = await session.list_tools()
            for tool in result.tools:
                tool_decl = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                active_tools.append(tool_decl)

        # 4. 初始化模型 (System Prompt)
        persona = config.get("persona", {})
        sys_prompt = f"""You are {persona.get('name', 'Polymath')}. {persona.get('role', 'Assistant')}.
        You are an intelligent Polymath, capable of handling diverse tasks using your tools.
        You communicate via the Model Context Protocol (MCP).
        Always use tools when you need to read memory, see images, or search data.
        """
        
        model = genai.GenerativeModel("gemini-1.5-pro", tools=[genai.protos.Tool(function_declarations=active_tools)])
        chat = model.start_chat(history=[], enable_automatic_function_calling=False) # 关闭自动调用，我们要手动接管

        console.print("[bold blue]Polymath v0.2 (MCP Architecture)[/bold blue]")
        console.print(f"[dim]Connected Servers: {', '.join(mcp_client.sessions.keys())}[/dim]")

        # 5. 聊天主循环
        while True:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # 发送消息
            with console.status("Thinking...", spinner="dots"):
                response = chat.send_message(user_input)
                
                # 处理可能的工具调用 (多轮)
                while True:
                    part = response.candidates[0].content.parts[0]
                    
                    # 检查是否有函数调用
                    if part.function_call:
                        fc = part.function_call
                        tool_name = fc.name
                        args = dict(fc.args)
                        
                        # 注入当前项目上下文 (如果是 memory 相关工具)
                        if tool_name in ["save_note", "search_notes"]:
                            args["collection_name"] = project

                        # --- 安全审批流 ---
                        if tool_name in SENSITIVE_TOOLS:
                            console.print(f"\n[bold red]⚠️  AI 请求执行敏感操作:[/bold red]")
                            console.print(f"[yellow]Tool:[/yellow] {tool_name}")
                            console.print(f"[yellow]Args:[/yellow] {json.dumps(args, indent=2, ensure_ascii=False)}")
                            
                            confirm = Prompt.ask("允许执行吗？", choices=["y", "n"], default="n")
                            if confirm.lower() != "y":
                                tool_result = "User denied the operation."
                                console.print("[red]已拒绝。[/red]")
                            else:
                                tool_result = await mcp_client.call_tool(tool_name, args)
                        else:
                            # 非敏感工具直接执行
                            console.print(f"[cyan]Calling Tool: {tool_name}...[/cyan]")
                            tool_result = await mcp_client.call_tool(tool_name, args)
                        
                        # --- 结束安全审批流 ---

                        console.print(f"[dim]Result: {str(tool_result)[:100]}...[/dim]")
                            
                        # 把结果喂回给模型
                        response = chat.send_message(
                            genai.protos.Content(
                                parts=[genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=tool_name,
                                        response={"result": tool_result}
                                    )
                                )]
                            )
                        )
                    else:
                        # 没有函数调用，说明是纯文本回复，打印并退出内层循环
                        console.print(f"\n[bold purple]Polymath:[/bold purple]\n{response.text}")
                        break

    finally:
        await mcp_client.cleanup()

@app.command()
def start(project: str = "default"):
    """启动 Polymath 并进入特定项目环境"""
    asyncio.run(chat_loop(project=project))

def entry_point():
    app()

if __name__ == "__main__":
    app()
