"""
File operations MCP server.
Provides file manipulation tools (move, copy, delete, rename).
"""

import os
import shutil
from mcp.server.fastmcp import FastMCP
from src.core.security import validate_path
from src.services import code_nav

mcp = FastMCP("PolymathFileSystemOperations")


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
def move_file(src: str, dst: str) -> str:
    """
    Move a file or directory to a new location.

    Args:
        src: Source path
        dst: Destination path

    Returns:
        Success message or error
    """
    src_path = validate_path(src)
    dst_path = validate_path(dst)

    if not os.path.exists(src_path):
        return f"Error: Source not found: {src}"

    try:
        # Create destination directory if needed
        dst_dir = os.path.dirname(dst_path)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)

        shutil.move(src_path, dst_path)
        return f"Successfully moved {src} to {dst}"

    except Exception as e:
        return f"Error moving file: {str(e)}"


@mcp.tool()
def copy_file(src: str, dst: str, overwrite: bool = False) -> str:
    """
    Copy a file or directory to a new location.

    Args:
        src: Source path
        dst: Destination path
        overwrite: Whether to overwrite if destination exists

    Returns:
        Success message or error
    """
    src_path = validate_path(src)
    dst_path = validate_path(dst)

    if not os.path.exists(src_path):
        return f"Error: Source not found: {src}"

    if os.path.exists(dst_path) and not overwrite:
        return f"Error: Destination already exists: {dst}. Use overwrite=True to replace."

    try:
        # Create destination directory if needed
        dst_dir = os.path.dirname(dst_path)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)

        if os.path.isdir(src_path):
            # Copy directory
            if os.path.exists(dst_path) and overwrite:
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            # Copy file
            shutil.copy2(src_path, dst_path)

        return f"Successfully copied {src} to {dst}"

    except Exception as e:
        return f"Error copying: {str(e)}"


@mcp.tool()
def delete_file(path: str, recursive: bool = False) -> str:
    """
    Delete a file or directory.

    WARNING: This operation is irreversible. Use with caution.

    Args:
        path: Path to delete
        recursive: If True, delete directories and their contents

    Returns:
        Success message or error
    """
    valid_path = validate_path(path)

    if not os.path.exists(valid_path):
        return f"Error: Path not found: {path}"

    try:
        if os.path.isdir(valid_path):
            if not recursive:
                return f"Error: {path} is a directory. Use recursive=True to delete it."

            shutil.rmtree(valid_path)
            return f"Successfully deleted directory: {path}"
        else:
            os.remove(valid_path)
            return f"Successfully deleted file: {path}"

    except Exception as e:
        return f"Error deleting: {str(e)}"


@mcp.tool()
def rename_file(old_path: str, new_name: str) -> str:
    """
    Rename a file or directory (in the same directory).

    Args:
        old_path: Current file path
        new_name: New name (just the name, not full path)

    Returns:
        Success message or error
    """
    old_valid_path = validate_path(old_path)

    if not os.path.exists(old_valid_path):
        return f"Error: File not found: {old_path}"

    try:
        # Build new path in same directory
        directory = os.path.dirname(old_valid_path)
        new_path = os.path.join(directory, new_name)
        new_valid_path = validate_path(new_path)

        if os.path.exists(new_valid_path):
            return f"Error: A file with name '{new_name}' already exists"

        os.rename(old_valid_path, new_valid_path)
        return f"Successfully renamed {old_path} to {new_name}"

    except Exception as e:
        return f"Error renaming: {str(e)}"


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
    import re
    import fnmatch
    
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
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
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

@mcp.tool()
def list_directory_tree(path: str = ".", depth: int = 2) -> str:
    """
    Show a recursive directory tree to understand project structure.
    
    Args:
        path: Root directory
        depth: Maximum recursion depth
    """
    valid_path = validate_path(path)
    
    def get_tree(current_path, current_depth):
        if current_depth > depth:
            return ""
        
        try:
            items = sorted(os.listdir(current_path))
        except Exception:
            return ""
            
        tree = ""
        for i, item in enumerate(items):
            if item.startswith('.'): continue
            
            full_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(full_path)
            
            indent = "  " * (depth - current_depth)
            tree += f"{indent}├── {item}{'/' if is_dir else ''}\n"
            
            if is_dir:
                tree += get_tree(full_path, current_depth + 1)
        return tree

    tree_output = get_tree(valid_path, 1)
    return f"Project Tree for {path}:\n{tree_output}" if tree_output else "Empty or inaccessible directory."

@mcp.tool()
def create_directory(path: str) -> str:
    """
    Create a new directory (and parent directories if needed).

    Args:
        path: Directory path to create

    Returns:
        Success message or error
    """
    valid_path = validate_path(path)

    try:
        os.makedirs(valid_path, exist_ok=True)
        return f"Successfully created directory: {path}"

    except Exception as e:
        return f"Error creating directory: {str(e)}"


if __name__ == "__main__":
    mcp.run()
