"""
Git Remote Operations

Provides remote repository operations:
- Fetch changes from remote
- Pull changes from remote
- Push changes to remote
"""

import logging

from mcp.server.fastmcp import FastMCP

from src.servers.git_common import is_git_repo as _is_git_repo
from src.servers.git_common import run_git_command as _run_git_command
from src.servers.git_common import validate_git_ref as _validate_git_ref

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("DoraemonGitRemote")


# ========================================
# Remote Operations Tools
# ========================================


@mcp.tool()
def git_pull(
    path: str = ".",
    remote: str = "origin",
    branch: str | None = None,
) -> str:
    """
    Pull changes from remote repository.

    Args:
        path: Repository path
        remote: Remote name (default: origin)
        branch: Branch to pull (default: current branch)

    Returns:
        Pull result or error message
    """
    if not _is_git_repo(path):
        return f"Error: {path} is not a git repository"

    # Validate remote name
    is_valid, error_msg = _validate_git_ref(remote)
    if not is_valid:
        return f"Error: Invalid remote '{remote}': {error_msg}"

    # Validate branch if provided
    if branch:
        is_valid, error_msg = _validate_git_ref(branch)
        if not is_valid:
            return f"Error: Invalid branch '{branch}': {error_msg}"

    args = ["pull", remote]
    if branch:
        args.append(branch)

    success, output = _run_git_command(args, cwd=path, timeout=60)
    return output if success else f"Error: {output}"


@mcp.tool()
def git_push(
    path: str = ".",
    remote: str = "origin",
    branch: str | None = None,
    set_upstream: bool = False,
) -> str:
    """
    Push commits to remote repository.

    Args:
        path: Repository path
        remote: Remote name (default: origin)
        branch: Branch to push (default: current branch)
        set_upstream: Set upstream tracking reference

    Returns:
        Push result or error message
    """
    if not _is_git_repo(path):
        return f"Error: {path} is not a git repository"

    # Validate remote name
    is_valid, error_msg = _validate_git_ref(remote)
    if not is_valid:
        return f"Error: Invalid remote '{remote}': {error_msg}"

    # Validate branch if provided
    if branch:
        is_valid, error_msg = _validate_git_ref(branch)
        if not is_valid:
            return f"Error: Invalid branch '{branch}': {error_msg}"

    args = ["push"]
    if set_upstream:
        args.append("-u")
    args.append(remote)
    if branch:
        args.append(branch)

    success, output = _run_git_command(args, cwd=path, timeout=60)
    return output if success else f"Error: {output}"


@mcp.tool()
def git_fetch(
    path: str = ".",
    remote: str = "origin",
    prune: bool = False,
) -> str:
    """
    Fetch changes from remote without merging.

    Args:
        path: Repository path
        remote: Remote name (default: origin)
        prune: Remove remote-tracking branches that no longer exist

    Returns:
        Fetch result or error message
    """
    if not _is_git_repo(path):
        return f"Error: {path} is not a git repository"

    args = ["fetch", remote]
    if prune:
        args.append("--prune")

    success, output = _run_git_command(args, cwd=path, timeout=60)
    return output if output else "Fetch completed (up to date)"


if __name__ == "__main__":
    mcp.run()
