import os
import asyncio
import json
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

# Google GenAI
import google.generativeai as genai
from google.generativeai.types import Tool as GenAITool

# 导入通用 MCP 客户端
from src.host.client import MultiServerMCPClient
# Core Imports
from src.core.config import load_config
from src.core.diff import print_diff
from src.core.prompts import get_system_prompt, PROMPTS

app = typer.Typer()
console = Console()

# 加载 .env 环境变量
load_dotenv()

# Global State for Mode
CURRENT_MODE = "default"

def init_chat_model(mode: str, tools: list, history: list = []):
    """Initialize the Gemini model with a specific mode (system prompt)."""
    config = load_config()
    persona = config.get("persona", {})
    
    # Get prompt for mode
    sys_instruction = get_system_prompt(mode, persona)
    
    # Load Project Memory if exists
    if os.path.exists("POLYMATH.md"):
        try:
            with open("POLYMATH.md", "r") as f:
                memory_content = f.read()
            sys_instruction += f"\n\n=== PROJECT MEMORY (POLYMATH.md) ===\n{memory_content}\n====================================\n"
        except Exception:
            pass

    model = genai.GenerativeModel("gemini-1.5-pro", 
                                 tools=[genai.protos.Tool(function_declarations=tools)],
                                 system_instruction=sys_instruction)
    
    return model.start_chat(history=history, enable_automatic_function_calling=False)

async def handle_slash_command(command: str, chat_session_ref: dict, mcp_client, active_tools) -> bool:
    """
    Handle slash commands. 
    chat_session_ref is a dict {"session": chat, "history": history} to allow modification.
    """
    global CURRENT_MODE
    cmd_parts = command.strip().split()
    cmd = cmd_parts[0].lower()

    if cmd == "/clear":
        console.print("[yellow]Clearing session history...[/yellow]")
        # Re-init with empty history
        chat_session_ref["session"] = init_chat_model(CURRENT_MODE, active_tools, [])
        return True
    
    elif cmd == "/init":
        console.print("[cyan]Initializing project memory (POLYMATH.md)...[/cyan]")
        content = """# Polymath Project Memory
Use this file to store project conventions, architectural decisions, and important notes.
Polymath will read this file to understand your coding style and preferences.

## Tech Stack
- Python 3.10+
- Google GenAI SDK

## Coding Style
- Use 4 spaces for indentation
- Type hints are required
"""
        with open("POLYMATH.md", "w") as f:
            f.write(content)
        console.print("[green]Created POLYMATH.md. Edit this file to guide the agent.[/green]")
        # Re-init to load the new file
        chat_session_ref["session"] = init_chat_model(CURRENT_MODE, active_tools, chat_session_ref["session"].history)
        return True

    elif cmd == "/mode":
        if len(cmd_parts) < 2:
            console.print(f"[red]Usage: /mode <{', '.join(PROMPTS.keys())}>[/red]")
            return True
            
        new_mode = cmd_parts[1].lower()
        if new_mode not in PROMPTS:
            console.print(f"[red]Invalid mode. Available: {', '.join(PROMPTS.keys())}[/red]")
            return True
            
        console.print(f"[green]Switching to {new_mode.upper()} mode...[/green]")
        CURRENT_MODE = new_mode
        
        # Preserve history but switch system prompt
        current_history = chat_session_ref["session"].history
        chat_session_ref["session"] = init_chat_model(new_mode, active_tools, current_history)
        return True

    elif cmd == "/help":
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        table.add_row("/mode <name>", "Switch agent persona (default, coder, architect)")
        table.add_row("/init", "Initialize project memory (POLYMATH.md)")
        table.add_row("/clear", "Clear conversation history")
        table.add_row("exit / quit", "End the session")
        console.print(table)
        return True

    return False


async def chat_loop(project: str = "default"):
    global CURRENT_MODE
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
    SENSITIVE_TOOLS = config.get("sensitive_tools", ["execute_python", "write_file", "save_note", "move_file", "delete_file"])

    try:
        # 3. 准备工具
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

        # 4. 初始化模型 (Initial Chat)
        # Wrap in a dict to allow reference update in handle_slash_command
        chat_ref = {
            "session": init_chat_model(CURRENT_MODE, active_tools, [])
        }

        console.print(Panel.fit(
            f"[bold blue]Polymath v0.4 (Multi-Mode)[/bold blue]\n"
            f"[dim]Servers: {', '.join(mcp_client.sessions.keys())}[/dim]\n"
            f"[dim]Type /help for commands. Current Mode: {CURRENT_MODE}[/dim]",
            border_style="blue"
        ))

        # 5. 聊天主循环
        turn_count = 0
        while True:
            # Show current mode in prompt
            mode_color = "green" if CURRENT_MODE == "default" else ("blue" if CURRENT_MODE == "coder" else "magenta")
            user_input = Prompt.ask(f"\n[bold {mode_color}]You ({CURRENT_MODE})[/bold {mode_color}]")
            
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # 处理 Slash Commands
            if user_input.startswith("/"):
                if await handle_slash_command(user_input, chat_ref, mcp_client, active_tools):
                    continue

            chat = chat_ref["session"]

            # 发送消息
            with console.status(f"[bold {mode_color}]Thinking ({CURRENT_MODE})...[/bold {mode_color}]", spinner="dots"):

                try:
                    response = chat.send_message(user_input)
                except Exception as e:
                    console.print(f"[red]API Error: {e}[/red]")
                    continue
                
                # 处理多轮对话 (Tool Loop)
                while True:
                    # Gemini 的响应可能包含多个 Part (Text + FunctionCall)
                    # 我们需要按顺序处理它们
                    
                    has_tool_call = False
                    tool_results = []
                    
                    # 遍历所有 parts
                    for part in response.candidates[0].content.parts:
                        
                        # 1. 处理思考文本 (Text)
                        if part.text:
                            # 渲染思考过程
                            console.print(Panel(Markdown(part.text), title="[bold purple]Thought[/bold purple]", border_style="purple", expand=False))
                            
                        # 2. 处理工具调用 (Function Call)
                        if part.function_call:
                            has_tool_call = True
                            fc = part.function_call
                            tool_name = fc.name
                            args = dict(fc.args)
                            
                            # 注入当前项目上下文
                            if tool_name in ["save_note", "search_notes"]:
                                args["collection_name"] = project

                            # --- Transparency: Diff View ---
                            if tool_name == "write_file" and "content" in args and "path" in args:
                                console.print(f"\n[bold yellow]📝 Proposing changes to:[/bold yellow] {args['path']}")
                                print_diff(args['path'], args['content'])

                            # --- Security: Approval ---
                            tool_result = None
                            if tool_name in SENSITIVE_TOOLS:
                                console.print(f"\n[bold red]⚠️  Sensitive Action:[/bold red] {tool_name}")
                                if tool_name != "write_file":
                                    console.print(f"[dim]Args: {json.dumps(args, indent=2, ensure_ascii=False)}[/dim]")
                                
                                confirm = Prompt.ask("Execute?", choices=["y", "n"], default="n")
                                if confirm.lower() != "y":
                                    tool_result = "User denied the operation."
                                    console.print("[red]Cancelled.[/red]")
                                else:
                                    console.print(f"[cyan]Running {tool_name}...[/cyan]")
                                    tool_result = await mcp_client.call_tool(tool_name, args)
                            else:
                                console.print(f"[cyan]Running {tool_name}...[/cyan]")
                                tool_result = await mcp_client.call_tool(tool_name, args)
                            
                            tool_results.append({
                                "name": tool_name,
                                "response": {"result": tool_result} 
                            })

                    # 如果没有工具调用，说明对话结束 (Wait for user input)
                    if not has_tool_call:
                        # Stats
                        turn_count += 1
                        usage = response.usage_metadata
                        if usage:
                            console.print(f"\n[dim italic]Turn {turn_count} | Input: {usage.prompt_token_count} | Output: {usage.candidates_token_count}[/dim italic]")
                        break
                    
                    # 如果有工具调用，将结果一次性发回给模型 (Gemini Client 支持 list of function_response 吗? 
                    # 标准做法是发回一个新的 Content，包含多个 FunctionResponse Parts)
                    
                    response_parts = []
                    for tr in tool_results:
                        response_parts.append(genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tr["name"],
                                response=tr["response"]
                            )
                        ))
                        
                    with console.status("[bold cyan]Processing Results...[/bold cyan]", spinner="dots"):
                        response = chat.send_message(genai.protos.Content(parts=response_parts))

    finally:
        await mcp_client.cleanup()

@app.command()
def setup():
    """初始化环境并安装依赖"""
    import subprocess
    console.print("[bold cyan]正在启动自动设置流程...[/bold cyan]")
    try:
        # 运行 shell 脚本
        subprocess.run(["bash", "scripts/setup.sh"], check=True)
    except Exception as e:
        console.print(f"[bold red]设置失败: {e}[/bold red]")

@app.command()
def start(project: str = "default"):
    """启动 Polymath 并进入特定项目环境"""
    # 简单的依赖检查
    try:
        import mcp
        import google.generativeai
    except ImportError:
        console.print("[yellow]警告: 核心依赖似乎未安装。请运行 'pl setup' 进行初始化。[/yellow]")
        if not Prompt.ask("是否继续启动？", choices=["y", "n"], default="n") == "y":
            return
            
    asyncio.run(chat_loop(project=project))

def entry_point():
    app()

if __name__ == "__main__":
    app()
