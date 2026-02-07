# 🤖 Doraemon Code

**Doraemon Code** is a powerful AI coding assistant built on the Model Context Protocol (MCP), designed to match and extend Claude Code's capabilities with a unified model gateway and comprehensive tooling.

[![Tests](https://img.shields.io/badge/tests-1500%2B%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## ✨ Key Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Doraemon Code Features                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  🌐 Multi-Provider    │  🔧 Unified Tools    │  💬 Smart Context           │
│  - Google Gemini      │  - read/write/search │  - Auto summarization       │
│  - OpenAI GPT-4       │  - 3 tools → 15 ops  │  - Per-model limits         │
│  - Anthropic Claude   │  - Occam's Razor     │  - Overflow recovery        │
│  - Ollama (local)     │                      │                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔄 Agentic Loop      │  🛡️ Safety           │  📦 Session Management      │
│  - Tool result → LLM  │  - Git safety        │  - Resume/continue          │
│  - Parallel execution │  - Shell hardening   │  - Fork/export              │
│  - Real streaming     │  - Permission system │  - Search history           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Interface                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   CLI (main)    │  │    Web UI       │  │   API Server    │             │
│  │  doraemon       │  │  localhost:3000 │  │  localhost:8000 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                              Host Layer                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Chat Loop    │  │ Tool Registry│  │ Context Mgr  │  │ Session Mgr  │    │
│  │ - Streaming  │  │ - 30+ tools  │  │ - Summarize  │  │ - Persist    │    │
│  │ - Agentic    │  │ - HITL       │  │ - Compress   │  │ - Resume     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Permissions  │  │ Checkpoints  │  │ Cost Tracker │  │ Hook System  │    │
│  │ - ALLOW/DENY │  │ - Snapshots  │  │ - Per model  │  │ - Events     │    │
│  │ - ASK/WARN   │  │ - Rollback   │  │ - Budgets    │  │ - Triggers   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                              Core Layer                                      │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        Model Client                                 │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │    │
│  │  │ Gateway Mode│  │ Direct Mode │  │ Streaming   │                 │    │
│  │  │ → Unified   │  │ → Provider  │  │ → Real-time │                 │    │
│  │  │   API       │  │   SDKs      │  │   Output    │                 │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Subagents    │  │ Parallel Exec│  │ Tool Select  │  │ Rules/Memory │    │
│  │ - Explore    │  │ - Dependency │  │ - Plan mode  │  │ - DORAEMON.md│    │
│  │ - Research   │  │ - Async      │  │ - Build mode │  │ - MEMORY.md  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                           MCP Servers (Capabilities)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Filesystem│ │   Git    │ │  Shell   │ │ Browser  │ │ Database │          │
│  │ read     │ │ status   │ │ execute  │ │ fetch    │ │ query    │          │
│  │ write    │ │ commit   │ │ bg tasks │ │ search   │ │ schema   │          │
│  │ search   │ │ diff/log │ │ safety   │ │ scrape   │ │ migrate  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                           Model Providers                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Google       │  │ OpenAI       │  │ Anthropic    │  │ Ollama       │    │
│  │ Gemini 2.5   │  │ GPT-4o       │  │ Claude 4.5   │  │ Local LLMs   │    │
│  │ Flash/Pro    │  │ GPT-4o-mini  │  │ Opus/Sonnet  │  │ Llama/etc    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/ifnodoraemon/doraemon-code.git
cd doraemon-code
pip install -e ".[dev]"

# Configure API keys
export GOOGLE_API_KEY=your_key
# or
export OPENAI_API_KEY=your_key
# or
export ANTHROPIC_API_KEY=your_key
```

### Basic Usage

```bash
# Start interactive session
doraemon

# Continue last session
doraemon -c

# Resume specific session (interactive picker)
doraemon --resume

# Resume by ID
doraemon --resume abc123

# Non-interactive mode
doraemon -p "Explain this code" < file.py

# With project isolation
doraemon --project MyProject
```

## 📋 CLI Reference

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--project` | `-p` | Project name for isolated sessions |
| `--resume` | `-r` | Resume session (ID, name, or picker) |
| `--continue` | `-c` | Continue most recent session |
| `--print` | | Non-interactive mode (exit after response) |
| `--max-turns` | | Limit conversation turns |
| `--verbose` | `-v` | Enable debug logging |
| `--allowedTools` | | Comma-separated allowed tools |
| `--disallowedTools` | | Comma-separated blocked tools |

### Slash Commands

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Core Commands                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ /help          Show all commands                                            │
│ /init          Create DORAEMON.md project file                              │
│ /mode <name>   Switch mode (plan/build)                                     │
│ /model [name]  Switch or list models                                        │
│ /status        Show system status                                           │
│ /config        Configure settings                                           │
│ /doctor        Run diagnostic checks                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Context Management                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ /context       Show context statistics                                      │
│ /clear         Clear conversation (keep summaries)                          │
│ /compact       Force context compression                                    │
│ /reset         Full reset                                                   │
│ /memory        Edit MEMORY.md files                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Session Management                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ /sessions      List recent sessions                                         │
│ /resume <id>   Resume a session                                             │
│ /rename <name> Rename current session                                       │
│ /export [path] Export conversation                                          │
│ /fork          Fork current session                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ History Navigation                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ /review        Show recent turns                                            │
│ /review <n>    Show last n turns                                            │
│ /review goto n Go back to turn n                                            │
│ /review search Search conversation                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Git Integration                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ /commit [msg]  Smart commit with auto-message                               │
│ /review-pr [n] View PR details                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ Other                                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ /tools         List available tools                                         │
│ /skills        Show loaded skills                                           │
│ /checkpoints   List file checkpoints                                        │
│ /rewind [id]   Restore to checkpoint                                        │
│ /cost          Show usage statistics                                        │
│ /exit          Exit                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Special Syntax

```bash
# File references - automatically expand to content
> Explain @./src/main.py
> Compare @./old.py and @./new.py

# Directory listing
> What's in @./src/

# Direct shell execution (bypass AI)
> !git status
> !ls -la

# Multi-line input
> """
  This is a
  multi-line prompt
  """
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DORAEMON_MODEL` | Default model | `gemini-3-pro-preview` |
| `DORAEMON_GATEWAY_URL` | Gateway server URL | (direct mode) |
| `GOOGLE_API_KEY` | Google Gemini API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `DORAEMON_DAILY_BUDGET` | Daily cost limit (USD) | 0 (unlimited) |
| `DORAEMON_SESSION_BUDGET` | Session cost limit | 0 (unlimited) |

### Project Files

```
project/
├── DORAEMON.md              # Project rules (like CLAUDE.md)
├── .doraemon/
│   ├── config.json          # Project configuration
│   ├── MEMORY.md            # Project memory
│   ├── permissions.json     # Permission rules
│   ├── hooks.json           # Event hooks
│   ├── sessions/            # Session storage
│   ├── conversations/       # Conversation history
│   └── checkpoints/         # File snapshots
└── ~/.doraemon/
    ├── config.json          # Global configuration
    └── MEMORY.md            # Global memory
```

## 🛡️ Safety Features

### Git Safety Protocol
- Blocks `git push --force`, `git reset --hard`, `git checkout .`, `git clean -f`
- Warns before destructive operations
- Prevents `--no-verify` flag

### Shell Hardening
- Command parsing with shlex
- Multi-command chain detection
- Blocked commands: `rm -rf /`, `mkfs`, `dd`, etc.
- Sensitive commands require confirmation

### Permission System
```json
{
  "rules": [
    {"action": "DENY", "tools": ["*"], "paths": ["**/.env", "**/*secret*"]},
    {"action": "ASK", "tools": ["shell_execute", "write"]},
    {"action": "ALLOW", "tools": ["read", "search"]}
  ]
}
```

## 📊 Data Flow

```
User Input
    │
    ├── @file references ──→ Expand to content
    │
    ▼
┌─────────────────┐
│ Command Handler │ ──→ /help, /mode, /commit, etc.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Manager │ ──→ Add to history, check limits
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Model Client   │ ──→ Stream response from LLM
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Tool Execution  │ ──→ Permission check → Execute → Results
└────────┬────────┘
         │
         ├── More tool calls? ──→ Loop back to Model Client
         │
         ▼
┌─────────────────┐
│ Display Output  │ ──→ Markdown rendering, stats
└─────────────────┘
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific module
pytest tests/core/test_context_manager.py -v

# Skip slow tests
pytest tests/ -m "not slow"
```

## 📂 Project Structure

```
src/
├── core/                    # Core infrastructure
│   ├── model_client.py      # Unified LLM interface
│   ├── model_client_direct.py # Direct provider APIs
│   ├── context_manager.py   # Conversation + summarization
│   ├── tool_selector.py     # Mode-based tool allocation
│   ├── permissions.py       # Permission rule engine
│   ├── parallel_executor.py # Parallel tool execution
│   ├── subagents.py         # Provider-agnostic subagents
│   ├── checkpoint.py        # File snapshots
│   ├── session.py           # Session persistence
│   ├── hooks.py             # Event system
│   └── rules.py             # DORAEMON.md + MEMORY.md
├── host/                    # CLI implementation
│   ├── cli/
│   │   ├── main.py          # Entry point + CLI args
│   │   ├── chat_loop.py     # Main loop + streaming
│   │   ├── commands_core.py # Slash commands
│   │   └── tool_execution.py # Tool execution + HITL
│   └── tools.py             # Tool registry
├── servers/                 # MCP servers
│   ├── filesystem.py        # read/write/search
│   ├── git.py               # Git operations
│   ├── shell.py             # Shell + safety
│   ├── browser.py           # Web browsing
│   └── database.py          # Database operations
├── gateway/                 # Model gateway
│   ├── server.py            # FastAPI server
│   └── adapters/            # Provider adapters
└── webui/                   # Web interface
```

## 🔄 Recent Improvements (v0.9.0)

### P0 - Critical Fixes
- ✅ Agentic tool loop: Results sent back to model
- ✅ Real streaming output with Rich Live
- ✅ Tool result truncation (30K chars)
- ✅ Context overflow auto-recovery

### P1 - High Impact
- ✅ Parallel tool execution with dependency analysis
- ✅ Git safety protocol
- ✅ Shell command hardening
- ✅ Per-model context windows
- ✅ Permission system integration

### P2 - Experience
- ✅ `--resume` interactive session picker
- ✅ `--continue` for most recent session
- ✅ `@file` reference syntax
- ✅ `/status`, `/config`, `/memory`, `/doctor` commands
- ✅ Tab completion for slash commands
- ✅ Multi-line input with `"""`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `pytest` and `ruff check`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Claude Code](https://claude.ai/code) - Inspiration
- [FastMCP](https://github.com/jlowin/fastmcp)
- [Rich](https://rich.readthedocs.io)

---

**Version**: 0.9.0 | **Status**: Active Development | **Python**: 3.10+
