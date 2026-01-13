# Polymath - AI Agent Project Overview

Polymath is an extensible, generalist AI agent built on the **Model Context Protocol (MCP)**. It follows a host-server architecture where a central host orchestrates specialized servers to perform tasks.

## Tech Stack
- **Language:** Python 3.10+
- **Protocol:** [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- **LLMs:** Google Gemini (via `google-generativeai`), OpenAI
- **CLI Framework:** [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/)
- **Vector DB:** [ChromaDB](https://www.trychroma.com/)
- **Search:** `duckduckgo-search`

## Project Structure
```
├── src/
│   ├── host/           # MCP Host implementation
│   │   ├── cli.py      # Main entry point (Typer CLI)
│   │   └── client.py   # MCP Client and LLM integration
│   ├── servers/        # Specialized MCP Servers
│   │   ├── computer.py # Code execution (Python)
│   │   ├── fs_read.py  # File reading (Text, PDF, Images via service)
│   │   ├── fs_write.py # File writing and management
│   │   ├── memory.py   # RAG and Long-term memory (ChromaDB)
│   │   └── web.py      # Web search capabilities
│   └── services/       # Shared Services
│       └── vision.py   # Vision processing logic
├── evals/          # Evaluation harness and datasets
└── agent.py        # Adapter for Google ADK Web UI
```

## Documentation
- [README.md](README.md): Basic setup and usage instructions.
- [DESIGN.md](DESIGN.md): Detailed architectural design and philosophy.
- [.polymath/STYLE.md](.polymath/STYLE.md): Content writing style guide for the agent.

## Development Commands
- **Installation:** `pip install -e .`
- **Run CLI:** `polymath` or `pl`
- **Run Tests:** `pytest`
- **Linting/Formatting:** (Follow project conventions, typically standard Python tools)

## Architecture & Design
- **Host (The Brain):** Manages the chat loop, tool orchestration, and Human-in-the-Loop (HITL) confirmations.
- **Servers (The Limbs):** Independent processes providing tools to the host via MCP.
- **Sandboxing:** File operations are restricted to `materials/` and `drafts/` directories.
- **Memory:** Uses RAG to store and retrieve project-specific information and user personas.

## Key Conventions
- **MCP Standards:** All tools must be exposed via MCP servers.
- **Type Hinting:** Use Python type hints throughout the codebase.
- **Asynchronous Code:** Extensive use of `asyncio` for MCP communication.
- **Safety:** Sensitive operations (execution, file writing) require user approval in the host.
