import os
import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown

# 导入我们的 Agent 定义
# 注意：实际运行时需要确保 src 在 pythonpath 中
try:
    from src.agent import ScribeAgent, kb
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from src.agent import ScribeAgent, kb

# 导入 ADK 的运行器 (假设使用 ADK 的 Model 接口，这里我们简化模拟)
# 由于 ADK 是个框架，通常需要一个 Runner。
# 为了简化 Phase 1，我们将手动模拟 Agent Loop，或者使用 ADK 自带的 run_agent
# 这里我们用最简单的 loop 来演示 Tool Calling 的逻辑 (伪代码层面的实现，对接真实 LLM)
import google.generativeai as genai
from google.generativeai import GenerativeModel

app = typer.Typer()
console = Console()

def get_agent_response(user_input: str, history: list):
    """
    这是一个简化的 Agent Loop，用于连接 ScribeAgent 的工具和 Gemini 模型。
    在真实 ADK 项目中，这一步通常由 adk.run() 接管。
    为了快速原型，我们这里手动桥接一下 (Native Mode)。
    """
    # 1. 初始化模型
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        console.print("[red]错误: 未设置 GOOGLE_API_KEY 环境变量。[/red]")
        return "请设置 API Key。"

    genai.configure(api_key=api_key)
    
    # 2. 绑定工具
    # 这是一个关键步骤：我们需要把 ScribeAgent 里的 @tool 函数转成 Gemini 可识别的 Tools
    scribe = ScribeAgent()
    tools = [
        scribe.read_style_guide,
        scribe.search_web,
        scribe.query_knowledge_base,
        scribe.ingest_material,
        scribe.list_materials,
        scribe.save_draft
    ]
    
    model = GenerativeModel("gemini-1.5-flash", tools=tools, system_instruction=scribe.__class__.__doc__)
    
    # 3. 发送请求 (带历史)
    chat = model.start_chat(history=history, enable_automatic_function_calling=True)
    response = chat.send_message(user_input)
    
    # 更新历史
    history.append({"role": "user", "parts": user_input})
    history.append(response.candidates[0].content)
    
    return response.text

@app.command()
def ingest(filename: str):
    """将 materials/ 目录下的文件索引到知识库"""
    scribe = ScribeAgent()
    result = scribe.ingest_material(filename)
    console.print(result)

@app.command()
def chat():
    """启动 Scribe 交互式对话"""
    console.print("[bold blue]Scribe Agent[/bold blue] (输入 'exit' 退出, 'clear' 清屏)")
    history = []
    
    while True:
        user_input = Prompt.ask("[bold green]You[/bold green]")
        
        if user_input.lower() in ["exit", "quit"]:
            break
        if user_input.lower() == "clear":
            history = []
            console.clear()
            continue
            
        with console.status("[bold yellow]Thinking...[/bold yellow]", spinner="dots"):
            try:
                response_text = get_agent_response(user_input, history)
                console.print("\n[bold purple]Scribe:[/bold purple]")
                console.print(Markdown(response_text))
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")

if __name__ == "__main__":
    app()
