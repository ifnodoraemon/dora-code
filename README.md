# Polymath (ex-Scribe)

**Polymath** 是一个基于 **MCP (Model Context Protocol)** 架构的通用 AI 智能体，旨在成为你的全能数字副手。它不仅能写作，还能阅读代码、分析数据、识别图像，并拥有长期记忆。

## 🌟 核心特性

*   **真正的 MCP 架构:** 采用 Client-Server 模式，能力无限扩展。
*   **多模态视觉 (Eyes):** 支持 **Gemini Vision** 和 **OpenAI GPT-4o**，支持 OCR 和图像理解。
*   **长期记忆 (Memory):** 基于 **ChromaDB** 的本地向量记忆库，支持按项目隔离。
*   **全能文件读写:** 支持 PDF, Word, PPT, Excel 及纯文本的深度解析与生成。
*   **代码执行 (Computer):** 内置 Python 解释器，可进行数据分析和绘图。
*   **安全沙箱:** 文件操作限制在项目目录内，敏感操作需人工审批 (HITL)。

## 🛠️ 安装

1.  **克隆仓库:**
    ```bash
    git clone <repo-url>
    cd polymath
    ```

2.  **创建并激活环境:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安装依赖:**
    ```bash
    pip install .
    ```

## ⚙️ 配置

1.  **创建环境变量文件 `.env`:**
    ```bash
    # 必填 (默认使用 Gemini)
    GOOGLE_API_KEY="your_google_api_key"
    
    # 选填 (如果想用 GPT-4o 进行视觉识别)
    OPENAI_API_KEY="your_openai_api_key"
    ```

2.  **配置 MCP Servers (`.polymath/config.json`):**
    默认已配置 Memory, Vision, Web, Filesystem, Computer 五大服务。
    你可以在此文件中修改视觉模型版本 (e.g., `gemini-1.5-pro`) 或切换 Provider (`google` -> `openai`).

## 🚀 使用方法

### 命令行模式 (CLI)
这是主要的交互方式。支持项目隔离。

```bash
# 启动默认项目
polymath start

# 启动特定项目 (记忆库独立)
polymath start --project "ProjectAlpha"
```

### Web 调试模式 (ADK)
使用 Google ADK 提供的 Web UI 可视化调试工具调用。

```bash
adk web src/agent.py
```

## 📂 项目结构

*   `src/host/`: MCP Client 主程序 (CLI)。
*   `src/servers/`: 独立的 MCP Servers (Memory, Vision, Filesystem, etc.)。
*   `materials/`: 默认的资料存放目录。
*   `drafts/`: AI 生成内容的默认保存目录。
*   `.polymath/`: 存储配置和长期记忆数据库。

## 🛡️ 安全机制

*   **HITL (Human-in-the-loop):** 当 AI 尝试执行代码、写文件或修改记忆时，CLI 会暂停并请求你的确认。
*   **Path Jailing:** 文件系统操作被限制在当前工作目录，防止越权访问。
