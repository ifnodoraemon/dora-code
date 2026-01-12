# Scribe Agent - Architecture Design Document

## 1. Project Overview
**Name:** Scribe Agent (`scribe-agent`)
**Goal:** A personal AI agent specializing in creating high-quality written materials (work reports, creative writing, articles) by adapting software engineering best practices (inspired by Claude Code & OpenCode).

## 2. Core Philosophy: "Docs as Code"
We treat writing projects with the same rigor as software projects:
- **Source of Truth:** Raw materials (PDFs, notes) are the "dependencies".
- **Iterative Process:** Plan -> Draft -> Review -> Refine -> Ship.
- **Configuration as Code:** Writing styles and preferences are stored in configuration files, not just prompt memories.

## 3. System Architecture

### 3.1 Directory Structure
```
scribe-agent/
├── materials/          # "Dependencies": Raw inputs (PDFs, text notes, research data)
├── drafts/             # "Src": Working drafts (Markdown format), version controlled
├── final/              # "Build": Polished, final outputs (PDF, Docx)
├── .scribe/            # "Config": Agent configuration
│   ├── STYLE.md        # The "System Prompt" - Tone, voice, formatting rules (cf. CLAUDE.md)
│   ├── PERSONAS.yaml   # Define specific writer personas (e.g., "Tech Blogger", "Corporate Professional")
│   └── MEMORY.json     # Long-term facts learned from user
├── src/                # The Agent's Source Code (Python)
│   ├── core/           # LLM interaction & Context Management
│   ├── tools/          # File I/O, Web Search, PDF Reading
│   └── cli.py          # Command Line Interface (using Click or Typer)
└── README.md
```

### 3.2 Key Modules (The "Agentic" Workflow)

#### A. The Context Engine (The "Mental Model")
Similar to how Claude Code scans a repo, Scribe scans the `materials/` folder.
- **Ingestion:** Automatically reads and summarizes files dropped into `materials/`.
- **Indexing:** Creates a lightweight index (tags/summary) to know what information is available.

#### B. The Workflow Commands (CLI)
We will implement a CLI that mimics a developer workflow:

1.  **`scribe research <topic>`**
    - Scours the web and `materials/` folder.
    - Generates a `research_brief.md` summary.

2.  **`scribe plan <topic>`**
    - Reads the research brief.
    - Generates a structural outline (e.g., `outline.md`).
    - *User Action:* User edits the outline to confirm direction.

3.  **`scribe draft <section>`**
    - Takes the outline and writes the content section by section.
    - Follows rules in `.scribe/STYLE.md`.

4.  **`scribe review <file>`**
    - The "Linter" for prose. Checks for logic gaps, tone consistency, and clarity.
    - Offers specific edit suggestions (diff view).

### 4. Technical Stack
- **Language:** Python 3.10+
- **Interface:** CLI (using `Rich` library for a beautiful TUI, like OpenCode).
- **LLM:** Google Gemini API (via system environment).
- **Storage:** Local Filesystem (Markdown driven).

## 5. Roadmap
- **Phase 1 (Foundation):** Setup project structure, basic CLI, and LLM connection.
- **Phase 2 (Context):** Implement file reading (PDF/Txt) and context injection.
- **Phase 3 (Workflow):** Implement Plan -> Draft -> Review loop.
- **Phase 4 (Polish):** Add Web Search and Style Config customization.
