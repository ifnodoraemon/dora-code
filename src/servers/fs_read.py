import os
import glob as glob_module
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from src.core.security import validate_path
from src.services import document, vision, outline

mcp = FastMCP("PolymathFileSystemReader")

@mcp.tool()
def read_file_outline(path: str) -> str:
    """
    Read the structural outline of a file (Classes, Functions) to understand code without reading the whole content.
    Highly recommended for exploring new files.
    
    Args:
        path: Path to the file (Python, JS, TS, etc.)
    """
    valid_path = validate_path(path)
    if not os.path.exists(valid_path):
        return "Error: File not found."
        
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
            if item.startswith('.') and not show_hidden:
                continue

            full_path = os.path.join(valid_path, item)

            if detailed:
                try:
                    stat = os.stat(full_path)

                    # Format size
                    size = _human_size(stat.st_size)

                    # Modified time
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                    # Type
                    if os.path.isdir(full_path):
                        ftype = "dir"
                        size = "<DIR>"
                    else:
                        ftype = "file"

                    entries.append(f"{item:<40} {size:>10} {mtime} [{ftype}]")
                except:
                    # Fallback if stat fails
                    entries.append(item)
            else:
                entries.append(item)

        if not entries:
            return "(empty directory)"

        return "\n".join(entries)

    except Exception as e:
        return f"Error: {e}"


def _human_size(bytes_size):
    """Convert bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}PB"

import itertools

@mcp.tool()
def read_file(path: str, offset: int = 0, limit: int = None, encoding: str = "utf-8") -> str:
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
                 with open(valid_path, "r", encoding=encoding, errors="replace") as f:
                     return f.read()
            
            with open(valid_path, "r", encoding=encoding, errors="replace") as f:
                # Use islice to efficiently skip to offset and read 'limit' lines
                # This avoids loading the entire file into memory
                iterator = itertools.islice(f, offset, offset + limit if limit else None)
                selected_lines = list(iterator)
                
                # We can't easily know total_lines without reading the whole file,
                # but for large files we strictly want to avoid that.
                # So we return what we have.
                
                if not selected_lines:
                    return f"No lines found at offset {offset}."

                result = f"[Lines {offset+1}-{offset+len(selected_lines)}]\n\n"
                result += "".join(selected_lines)
                
                if limit and len(selected_lines) == limit:
                     # Peek if there is more (optimization: simplistic check)
                     result += f"\n\n[... (more lines may exist)]"

                return result

    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def glob_files(pattern: str, exclude: list[str] = None, max_results: int = 1000) -> str:
    """
    Find files matching a glob pattern.

    Supports wildcards:
    - * matches any characters
    - ** matches any directories (recursive)
    - ? matches single character
    - [abc] matches one character in brackets

    Args:
        pattern: Glob pattern (e.g., "**/*.py", "src/**/test_*.py")
        exclude: List of patterns to exclude (e.g., ["**/node_modules/**", "**/__pycache__/**"])
        max_results: Maximum number of files to return (default: 1000)

    Examples:
        glob_files("**/*.py")  # All Python files recursively
        glob_files("src/**/*.js")  # All JS files in src/
        glob_files("*.{py,js}")  # All .py and .js files in current dir

    Returns:
        Newline-separated list of matching file paths
    """
    try:
        # Find matching files
        matches = glob_module.glob(pattern, recursive=True)

        # Apply exclusions
        if exclude:
            filtered = []
            for match in matches:
                # Check if match should be excluded
                should_exclude = False
                for excl_pattern in exclude:
                    if glob_module.fnmatch.fnmatch(match, excl_pattern):
                        should_exclude = True
                        break

                if not should_exclude:
                    filtered.append(match)

            matches = filtered

        # Limit results
        if len(matches) > max_results:
            matches = matches[:max_results]
            truncated = True
        else:
            truncated = False

        # Sort for consistent output
        matches = sorted(matches)

        if not matches:
            return f"No files found matching pattern: {pattern}"

        result = "\n".join(matches)

        if truncated:
            result += f"\n\n[Showing first {max_results} of {len(matches)} matches]"
        else:
            result = f"Found {len(matches)} file(s):\n\n" + result

        return result

    except Exception as e:
        return f"Error in glob search: {str(e)}"


if __name__ == "__main__":
    mcp.run()