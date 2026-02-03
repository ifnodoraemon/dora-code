"""
Filesystem Read Operations Module

Provides read-only file operations:
- read_file: Read file content with optional offset/limit
- read_file_outline: Get structural outline of code files
- list_directory: List directory contents
- list_directory_tree: Show recursive directory tree
- find_symbol: Find class/function definitions
"""

import itertools
import logging
import os
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from src.core.security import validate_path
from src.services import code_nav, document, outline, vision

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("DoraemonFilesystemRead")


def _human_size(bytes_size: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}PB"


@mcp.tool()
def read_file_outline(path: str) -> str:
    """
    Read the structural outline of a file (Classes, Functions) to understand code without reading the whole content.
    Highly recommended for exploring new files.

    Args:
        path: Path to the file (Python, JS, TS, etc.)
    """
    try:
        valid_path = validate_path(path)
    except (PermissionError, ValueError) as e:
        logger.warning(f"Path validation failed for '{path}': {e}")
        return f"Error: {e}"

    if not os.path.exists(valid_path):
        logger.warning(f"File not found: {valid_path}")
        return "Error: File not found."

    logger.debug(f"Reading outline of: {valid_path}")
    return outline.parse_outline(valid_path)


@mcp.tool()
def list_directory(path: str = ".", show_hidden: bool = False, detailed: bool = True) -> str:
    """
    List files and directories at the given path.

    Args:
        path: Directory path to list
        show_hidden: Include hidden files (starting with .)
        detailed: Show detailed metadata (size, modified time, type)

    Returns:
        Formatted directory listing
    """
    valid_path = validate_path(path)
    if not os.path.exists(valid_path):
        return "Error: Path not found."

    try:
        entries = []

        for item in sorted(os.listdir(valid_path)):
            # Skip hidden files if requested
            if item.startswith(".") and not show_hidden:
                continue

            full_path = os.path.join(valid_path, item)

            if detailed:
                try:
                    stat = os.stat(full_path)
                    size = _human_size(stat.st_size)
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                    # Type
                    if os.path.isdir(full_path):
                        ftype = "dir"
                        size = "<DIR>"
                    else:
                        ftype = "file"

                    entries.append(f"{item:<40} {size:>10} {mtime} [{ftype}]")
                except OSError:
                    # Fallback if stat fails
                    entries.append(item)
            else:
                entries.append(item)

        if not entries:
            return "(empty directory)"

        return "\n".join(entries)

    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def read_file(path: str, offset: int = 0, limit: int | None = None, encoding: str = "utf-8") -> str:
    """
    Intelligently read a file with optional partial reading.
    Supports: .txt, .md, .py, .pdf, .docx, .pptx, .xlsx, .png, .jpg

    Args:
        path: File path to read
        offset: Starting line number (0-based, for text files only)
        limit: Maximum number of lines to read (for text files only)
        encoding: Text encoding (default: utf-8)

    Returns:
        File content or error message
    """
    valid_path = validate_path(path)
    if not os.path.exists(valid_path):
        return "Error: File not found."

    ext = os.path.splitext(path)[1].lower()

    try:
        # Document formats (no offset/limit support)
        if ext == ".pdf":
            return document.parse_pdf(valid_path)
        elif ext == ".docx":
            return document.parse_docx(valid_path)
        elif ext == ".pptx":
            return document.parse_pptx(valid_path)
        elif ext in [".xlsx", ".xls"]:
            return document.parse_xlsx(valid_path)

        # Image formats
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            return vision.process_image(valid_path)

        # Text formats (support offset/limit)
        else:
            if offset == 0 and limit is None:
                with open(valid_path, encoding=encoding, errors="replace") as f:
                    return f.read()

            with open(valid_path, encoding=encoding, errors="replace") as f:
                # Use islice to efficiently skip to offset and read 'limit' lines
                iterator = itertools.islice(f, offset, offset + limit if limit else None)
                selected_lines = list(iterator)

                if not selected_lines:
                    return f"No lines found at offset {offset}."

                result = f"[Lines {offset + 1}-{offset + len(selected_lines)}]\n\n"
                result += "".join(selected_lines)

                if limit and len(selected_lines) == limit:
                    result += "\n\n[... (more lines may exist)]"

                return result

    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def find_symbol(symbol: str, path: str = ".") -> str:
    """
    Find the DEFINITION of a class or function (Semantic Search).
    Use this instead of grep when you want to know "Where is class X defined?".

    Args:
        symbol: The name of the class or function (e.g., "MultiServerMCPClient")
        path: Root directory to search (default: current dir)
    """
    valid_path = validate_path(path)
    return code_nav.find_definition(valid_path, symbol)


@mcp.tool()
def list_directory_tree(path: str = ".", depth: int = 2) -> str:
    """
    Show a recursive directory tree to understand project structure.

    Args:
        path: Root directory
        depth: Maximum recursion depth (max: 10)
    """
    # Limit depth to prevent excessive recursion
    depth = min(max(1, depth), 10)
    valid_path = validate_path(path)

    def get_tree(current_path: str, current_depth: int) -> str:
        if current_depth > depth:
            return ""

        try:
            items = sorted(os.listdir(current_path))
        except Exception:
            return ""

        tree = ""
        for item in items:
            if item.startswith("."):
                continue

            full_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(full_path)

            indent = "  " * (depth - current_depth)
            tree += f"{indent}├── {item}{'/' if is_dir else ''}\n"

            if is_dir:
                tree += get_tree(full_path, current_depth + 1)
        return tree

    tree_output = get_tree(valid_path, 1)
    return (
        f"Project Tree for {path}:\n{tree_output}"
        if tree_output
        else "Empty or inaccessible directory."
    )


if __name__ == "__main__":
    mcp.run()
