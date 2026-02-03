"""
Filesystem Search Operations Module

Provides file search operations:
- glob_files: Find files matching glob patterns
- grep_search: Search for text patterns in files
"""

import fnmatch
import glob as glob_module
import logging
import os
import re

from mcp.server.fastmcp import FastMCP

from src.core.security import validate_path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("DoraemonFilesystemSearch")


@mcp.tool()
def glob_files(pattern: str, exclude: list[str] | None = None, max_results: int = 1000) -> str:
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
        # Security check: prevent path traversal in pattern
        if '..' in pattern:
            return "Error: Pattern cannot contain '..' for security reasons."

        # Validate pattern doesn't start with absolute path or escape workspace
        if pattern.startswith('/') or pattern.startswith('~'):
            return "Error: Pattern cannot be an absolute path."

        # Find matching files
        matches = glob_module.glob(pattern, recursive=True)

        # Filter out results that are outside the workspace
        validated_matches = []
        for match in matches:
            try:
                # Validate each matched path is within workspace
                validate_path(match)
                validated_matches.append(match)
            except (PermissionError, ValueError):
                # Skip paths outside workspace
                continue
        matches = validated_matches

        # Apply exclusions
        if exclude:
            filtered = []
            for match in matches:
                # Check if match should be excluded
                should_exclude = False
                for excl_pattern in exclude:
                    if fnmatch.fnmatch(match, excl_pattern):
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


@mcp.tool()
def grep_search(pattern: str, include: str = "*", path: str = ".") -> str:
    """
    Search for a text pattern within files (recursive).
    Similar to 'grep -r'. Useful for finding where a variable or function is defined.

    Args:
        pattern: Regex pattern to search for
        include: Glob pattern for files to include (e.g. "*.py")
        path: Directory to search in
    """
    valid_path = validate_path(path)
    results = []

    try:
        regex = re.compile(pattern)

        for root, _, files in os.walk(valid_path):
            for file in files:
                if not fnmatch.fnmatch(file, include):
                    continue

                full_path = os.path.join(root, file)
                try:
                    with open(full_path, encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                # Format: path/to/file:line_num:content
                                rel_path = os.path.relpath(full_path, valid_path)
                                results.append(f"{rel_path}:{i}:{line.strip()}")

                                if len(results) >= 100:  # Hard limit to prevent massive outputs
                                    results.append("... (limit reached)")
                                    return "\n".join(results)
                except Exception:
                    # Skip binary or unreadable files
                    continue

        if not results:
            return f"No matches found for '{pattern}'."

        return "\n".join(results)

    except Exception as e:
        return f"Error searching: {str(e)}"


if __name__ == "__main__":
    mcp.run()
