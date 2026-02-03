"""
Doraemon Unified Filesystem MCP Server

A comprehensive filesystem server that combines all file operations:
- Reading: read_file, read_file_outline, list_directory, list_directory_tree, find_symbol
- Searching: glob_files, grep_search
- Writing: write_file
- Editing: edit_file, edit_file_multiline
- Operations: move_file, copy_file, delete_file, rename_file, create_directory

This is the main entry point that imports and re-exports tools from specialized modules:
- filesystem_read.py: Read-only operations
- filesystem_search.py: File search operations
- filesystem_write.py: Write operations
- filesystem_edit.py: File editing operations
- filesystem_ops.py: File manipulation operations
"""

from mcp.server.fastmcp import FastMCP

# Import security utilities
from src.core.security import validate_path

# Import all tools from specialized modules
from src.servers.filesystem_read import (
    _human_size,
    find_symbol,
    list_directory,
    list_directory_tree,
    read_file,
    read_file_outline,
)
from src.servers.filesystem_search import glob_files, grep_search
from src.servers.filesystem_write import write_file
from src.servers.filesystem_edit import edit_file, edit_file_multiline
from src.servers.filesystem_ops import (
    copy_file,
    create_directory,
    delete_file,
    move_file,
    rename_file,
)

# Create main MCP server
mcp = FastMCP("DoraemonFilesystem")

# Re-export all tools through the main server
mcp.tool()(read_file_outline)
mcp.tool()(list_directory)
mcp.tool()(read_file)
mcp.tool()(find_symbol)
mcp.tool()(glob_files)
mcp.tool()(grep_search)
mcp.tool()(list_directory_tree)
mcp.tool()(write_file)
mcp.tool()(edit_file)
mcp.tool()(edit_file_multiline)
mcp.tool()(move_file)
mcp.tool()(copy_file)
mcp.tool()(delete_file)
mcp.tool()(rename_file)
mcp.tool()(create_directory)

# Export all functions for backward compatibility
__all__ = [
    # Security utilities
    "validate_path",
    # Utilities
    "_human_size",
    # Read operations
    "read_file_outline",
    "list_directory",
    "read_file",
    "find_symbol",
    # Search operations
    "glob_files",
    "grep_search",
    "list_directory_tree",
    # Write operations
    "write_file",
    # Edit operations
    "edit_file",
    "edit_file_multiline",
    # File operations
    "move_file",
    "copy_file",
    "delete_file",
    "rename_file",
    "create_directory",
]

if __name__ == "__main__":
    mcp.run()
