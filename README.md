# 🤖 Doraemon Code

> **"从口袋里掏出任何你需要的工具"** — 像哆啦A梦一样，为开发者提供无限可能

Doraemon Code 是一个**本地优先**的 AI 编码助手，基于 MCP (Model Context Protocol) 架构，支持多种 LLM 提供商，专注于**简洁、安全、可扩展**。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🎯 核心理念

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   "如无必要，勿增实体" — 奥卡姆剃刀                                          │
│                                                                              │
│   我们相信：                                                                 │
│   • 3 个设计良好的工具 > 15 个分散的工具                                    │
│   • 直接函数调用 > 跨进程 JSON-RPC                                          │
│   • 本地运行 > 云端依赖                                                     │
│   • 安全默认 > 事后补救                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 为什么选择 Doraemon Code？

| 特性 | Claude Code | Doraemon Code |
|------|-------------|---------------|
| **模型支持** | 仅 Anthropic | Google/OpenAI/Anthropic/Ollama |
| **运行方式** | 云端 | **本地优先** |
| **工具架构** | 15+ 分散工具 | **3 核心 + 扩展** |
| **进程模型** | 多进程 MCP | **单进程直调** |
| **开源** | 否 | **是** |

---

## ⚡ 30 秒快速开始

```bash
# 安装
git clone https://github.com/ifnodoraemon/doraemon-code.git
cd doraemon-code && pip install -e .

# 配置 (任选一个)
export GOOGLE_API_KEY=your_key      # Google Gemini
export OPENAI_API_KEY=your_key      # OpenAI
export ANTHROPIC_API_KEY=your_key   # Anthropic

# 启动
doraemon
```

---

## 🏗️ 架构精髓

### 1. 统一工具设计 (Occam's Razor)

```
传统方式 (15个工具):              Doraemon 方式 (3个工具):
┌──────────────────┐             ┌──────────────────┐
│ read_file        │             │                  │
│ read_lines       │             │  read(mode=...)  │
│ list_directory   │  ────────>  │  • file          │
│ list_tree        │             │  • directory     │
│ get_outline      │             │  • outline       │
└──────────────────┘             │  • tree          │
┌──────────────────┐             └──────────────────┘
│ write_file       │             ┌──────────────────┐
│ edit_file        │             │                  │
│ delete_file      │  ────────>  │ write(op=...)    │
│ move_file        │             │  • create        │
│ copy_file        │             │  • edit          │
└──────────────────┘             │  • delete/move   │
┌──────────────────┐             └──────────────────┘
│ grep_search      │             ┌──────────────────┐
│ glob_files       │  ────────>  │ search(mode=...) │
│ find_symbol      │             │  • content/files │
└──────────────────┘             └──────────────────┘

结果: 80% 代码减少，100% 功能保留
```

### 2. 零开销工具调用

```
标准 MCP:                        Doraemon Code:
┌────────┐    JSON-RPC    ┌────────┐     ┌────────────────────────┐
│  Host  │ ──────────────>│ Server │     │        Host            │
│        │    ~10ms       │(进程)  │     │  ┌──────────────────┐  │
└────────┘<───────────────└────────┘     │  │ tool_function()  │  │
                                         │  │     ~0ms         │  │
                                         │  └──────────────────┘  │
                                         └────────────────────────┘

每次工具调用节省 10ms，100 次调用 = 1 秒
```

### 3. 多 Provider 统一接口

```python
# 一套代码，多个后端
from src.core.model_client import ModelClient

client = await ModelClient.create()  # 自动检测 Provider

# 相同的 API，不同的模型
response = await client.chat(messages, tools)
# 底层自动适配: Gemini / GPT-4 / Claude / Ollama
```

---

## 🛡️ 安全优先

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           安全防护层                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Git 安全协议                    Shell 硬化                                  │
│  ├─ 🚫 git push --force         ├─ 🚫 rm -rf /                              │
│  ├─ 🚫 git reset --hard         ├─ 🚫 mkfs, dd                              │
│  ├─ 🚫 git checkout .           ├─ ⚠️ sudo (需确认)                         │
│  └─ 🚫 --no-verify              └─ 🔍 多命令链检测                          │
│                                                                              │
│  敏感路径保护                    权限系统                                    │
│  ├─ 🔒 .env, .aws/*             ├─ ALLOW: read, search                      │
│  ├─ 🔒 *secret*, *password*     ├─ ASK: write, shell                        │
│  └─ 🔒 ~/.ssh/*, token*         └─ DENY: 敏感路径                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 功能对照表

### CLI 参数

```bash
doraemon                      # 交互模式
doraemon -c                   # 继续上次会话
doraemon --resume             # 选择历史会话
doraemon --resume abc123      # 恢复指定会话
doraemon -p "query"           # 非交互模式
doraemon --max-turns 5        # 限制轮次
doraemon --project MyProject  # 项目隔离
```

### Slash 命令

| 命令 | 功能 | 命令 | 功能 |
|------|------|------|------|
| `/help` | 帮助 | `/status` | 系统状态 |
| `/mode` | 切换模式 | `/config` | 配置设置 |
| `/clear` | 清空对话 | `/doctor` | 诊断检查 |
| `/compact` | 压缩上下文 | `/memory` | 编辑记忆 |
| `/commit` | 智能提交 | `/review` | 历史导航 |
| `/sessions` | 会话列表 | `/resume` | 恢复会话 |

### 特殊语法

```bash
@./src/main.py    # 引用文件内容
@./src/           # 引用目录结构
!git status       # 直接执行 shell
"""多行输入"""    # 多行模式
```

---

## 🔧 39 个内置工具

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 核心 (6)        │ Shell (4)       │ Git (5)         │ LSP (6)              │
│ read            │ shell_execute   │ git_status      │ lsp_diagnostics      │
│ write           │ shell_background│ git_diff        │ lsp_completions      │
│ search          │ execute_python  │ git_log         │ lsp_hover            │
│ notebook_read   │ install_package │ git_add         │ lsp_references       │
│ notebook_edit   │                 │ git_commit      │ lsp_rename           │
│ multi_edit      │                 │                 │ lsp_definition       │
├─────────────────┼─────────────────┼─────────────────┼──────────────────────┤
│ Lint (8)        │ Search (2)      │ Web (2)         │ Task (3)             │
│ lint_python_ruff│ semantic_search │ fetch_url       │ task_create          │
│ format_python   │ index_codebase  │ web_search      │ task_list            │
│ typecheck_mypy  │                 │                 │ task_update_status   │
│ lint_eslint     │ Memory (2)      │ System (1)      │                      │
│ lint_all        │ save_note       │ switch_mode     │                      │
│ code_complexity │ search_notes    │                 │                      │
│ check_security  │                 │                 │                      │
│ get_lint_summary│                 │                 │                      │
└─────────────────┴─────────────────┴─────────────────┴──────────────────────┘
```

---

## 📁 项目结构

```
doraemon-code/
├── src/
│   ├── core/                 # 核心基础设施
│   │   ├── model_client.py   # 统一 LLM 接口
│   │   ├── context_manager.py# 上下文 + 自动摘要
│   │   ├── permissions.py    # 权限规则引擎
│   │   └── ...
│   ├── host/                 # CLI 实现
│   │   ├── cli/main.py       # 入口 + 参数
│   │   ├── cli/chat_loop.py  # 主循环 + 流式
│   │   └── tools.py          # 工具注册表
│   ├── servers/              # MCP 服务器 (能力)
│   │   ├── filesystem_unified.py  # read/write/search
│   │   ├── shell.py          # Shell + 安全
│   │   ├── git.py            # Git 操作
│   │   └── ...
│   └── gateway/              # 模型网关 (可选)
├── tests/                    # 测试套件
├── DORAEMON.md              # 项目规则 (类似 CLAUDE.md)
└── .doraemon/               # 项目配置
    ├── MEMORY.md            # 项目记忆
    ├── config.json          # 配置
    └── sessions/            # 会话存储
```

---

## 🔄 数据流

```
用户输入 ──> @file 展开 ──> 命令处理 ──> 上下文管理 ──> LLM 调用
                                                          │
                                                          ▼
显示输出 <── Markdown 渲染 <── 权限检查 <── 工具执行 <── 工具调用
     │                              │
     │                              └── 循环直到无工具调用
     └── 统计信息 (tokens, cost, context%)
```

---

## 🚀 高级用法

### 项目配置 (DORAEMON.md)

```markdown
# 项目规则

## 技术栈
- Python 3.10+, FastAPI, PostgreSQL

## 代码风格
- 使用 ruff 格式化
- 类型注解必须

## 禁止操作
- 不要修改 migrations/
- 不要直接操作生产数据库
```

### 权限规则 (.doraemon/permissions.json)

```json
{
  "rules": [
    {"action": "DENY", "paths": ["**/.env", "**/secrets/*"]},
    {"action": "ASK", "tools": ["shell_execute", "write"]},
    {"action": "ALLOW", "tools": ["read", "search"]}
  ]
}
```

### 事件钩子 (.doraemon/hooks.json)

```json
{
  "hooks": [
    {
      "event": "pre_tool_call",
      "tool": "git_commit",
      "command": "ruff check . --fix"
    }
  ]
}
```

---

## 📊 与 Claude Code 对比

| 功能 | Claude Code | Doraemon Code |
|------|-------------|---------------|
| `--resume` 交互选择器 | ✅ | ✅ |
| `--continue` 继续会话 | ✅ | ✅ |
| `@file` 文件引用 | ✅ | ✅ |
| `/doctor` 诊断 | ✅ | ✅ |
| `/memory` 编辑 | ✅ | ✅ |
| Notebook 支持 | ✅ | ✅ |
| MultiEdit | ✅ | ✅ |
| 多 Provider | ❌ | ✅ |
| 本地运行 | ❌ | ✅ |
| 开源 | ❌ | ✅ |

---

## 🛠️ 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/ --fix
ruff format src/

# 类型检查
mypy src/
```

---

## 📄 License

MIT License - 自由使用、修改、分发

---

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io) - 架构基础
- [Claude Code](https://claude.ai/code) - 功能灵感
- [Rich](https://rich.readthedocs.io) - 终端美化

---

<div align="center">

**Doraemon Code** — 你的口袋里的 AI 编码助手 🎒

*Built with ❤️ for developers who value simplicity and power*

</div>
