# Polymath - Architecture Design Document

## 1. Project Overview
**Name:** Polymath (formerly Scribe Agent)
**Goal:** An extensible, generalist AI agent built on the **Model Context Protocol (MCP)**. It acts as a "Host" that orchestrates various specialized "Servers" (Memory, Vision, Compute, etc.) to assist users with writing, coding, and analysis tasks.

## 2. Core Philosophy: "Agent as a Platform"
Instead of a monolithic script, Polymath is designed as a platform:
- **Host (Client):** The brain. It manages the LLM context, routes tool calls, and handles user interaction.
- **Servers (Plugins):** The limbs. Standalone processes that expose capabilities via JSON-RPC (MCP Standard).
- **Project-Centric:** All memories and file operations are scoped to a specific "Project" context.

## 3. System Architecture

### 3.1 Directory Structure
```
polymath/
├── .polymath/          # Configuration & Data
│   ├── config.json     # MCP Server registry & Persona config
│   └── chroma_db/      # Vector Database (Long-term Memory)
├── materials/          # Input sandbox
├── drafts/             # Output sandbox
├── src/
│   ├── core/           # Core configurations and utilities
│   ├── evals/          # Evaluation harness and datasets
│   ├── host/           # [The Brain] - MCP Host implementation
│   │   ├── cli.py      # Main entry point (Typer CLI)
│   │   └── client.py   # MCP Client and LLM integration
│   ├── servers/        # [The Limbs] - Specialized MCP Servers
│   │   ├── computer.py # Code execution (Python)
│   │   ├── fs_edit.py  # File editing
│   │   ├── fs_ops.py   # File system operations
│   │   ├── fs_read.py  # File reading (PDF, Docx, etc.)
│   │   ├── fs_write.py # File writing and management
│   │   ├── memory.py   # RAG and Long-term memory
│   │   └── web.py      # Web search capabilities
│   ├── services/       # Shared business logic/services
│   └── agent.py        # Adapter for Google ADK Web UI
└── pyproject.toml      # Dependency Management
```

### 3.2 Key Components

#### A. The Host (CLI)
- **Role:** Connects to servers defined in `config.json`, aggregates tools, converts them to Gemini Function Declarations, and manages the chat loop.
- **Security:** Implements **Human-in-the-loop (HITL)** approval for sensitive actions (exec, write).

#### B. The Servers
1.  **Memory Server:**
    - Tech: ChromaDB + SentenceTransformers.
    - Features: `save_note`, `search_notes` (scoped by `collection_name`), `update_user_persona`.
2.  **Vision Service (Internal):**
    - Tech: Multi-vendor adapter (Gemini / OpenAI).
    - Features: Image processing integrated into `read_file` (Filesystem Server).
3.  **Filesystem Server:**
    - Tech: `pdfplumber`, `python-docx`, `openpyxl`.
    - Features: Format-aware `read_file`, sandboxed `write_file`.
4.  **Computer Server:**
    - Tech: `subprocess`.
    - Features: `execute_python`.

## 4. Security Model
- **Path Sandboxing:** The `Filesystem` server validates that all paths resolve within the project root.
- **Execution Gates:** High-risk tools (`execute_python`, `write_file`) trigger a user confirmation prompt in the CLI.

## 5. Roadmap
- **Phase 1:** Basic CLI & RAG (Completed).
- **Phase 2:** MCP Architecture Refactor (Completed).
- **Phase 3:** Multi-modal & Code Execution (Completed).
- **Phase 4:** Governance & Project Isolation (Completed).
- **Future:** Remote MCP Server support (e.g., connecting to a server running in Docker).