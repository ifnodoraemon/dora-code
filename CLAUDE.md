# CLAUDE.md

This repository has two product modes only:

- `plan`
- `build`

Current default built-in capability groups:

- `plan`
  - `read`
  - `memory`
  - `research`
  - `task`
- `build`
  - `read`
  - `edit`
  - `memory`
  - `research`
  - `task`

Built-in tool names in active mainline:

- `read`
- `search`
- `ask_user`
- `write`
- `run`
- `memory_get`
- `memory_put`
- `memory_search`
- `memory_list`
- `web_search`
- `web_fetch`
- `task`

Browser and database are not part of the default built-in mainline. They belong to extensions / MCP.

Provider runtime:

- OpenAI official SDK
- Anthropic official SDK
- Google official SDK

Remote MCP runtime:

- `streamable_http`
- `stdio`

Current MCP runtime behavior:

- fail-open
- retry
- failure cooldown
- `mcp-session-id` reuse for streamable HTTP

When updating docs in this repo:

- remove historical explanations
- remove deleted modules from docs
- do not document aspirational architecture as current behavior
- prefer current file paths and current runtime behavior
