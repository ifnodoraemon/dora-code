"""
Git Branch Management Operations

Provides branch-related git operations:
- List branches
- Create and delete branches
- Switch branches (checkout)
- Merge branches
"""

import logging

from mcp.server.fastmcp import FastMCP

from src.servers.git_common import is_git_repo as _is_git_repo
from src.servers.git_common import run_git_command as _run_git_command
from src.servers.git_common import validate_git_ref as _validate_git_ref

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("DoraemonGitBranch")


# ========================================
# Branch Management Tools
# ========================================


@mcp.tool()
def git_branch(
    path: str = ".",
    all_branches: bool = False,
) -> str:
    """
    List branches in the repository.

    Args:
        path: Repository path
        all_branches: Include remote branches

    Returns:
        List of branches (current branch marked with *)
    """
    if not _is_git_repo(path):
        return f"Error: {path} is not a git repository"

    args = ["branch"]
    if all_branches:
        args.append("-a")

    success, output = _run_git_command(args, cwd=path)
    return output if success else f"Error: {output}"


@mcp.tool()
def git_checkout(
    target: str,
    path: str = ".",
    create: bool = False,
) -> str:
    """
    Switch branches or restore files.

    Args:
        target: Branch name, commit hash, or file path
        path: Repository path
        create: If True, create a new branch with this name

    Returns:
        Confirmation or error message

    Examples:
        git_checkout("main")  # Switch to main branch
        git_checkout("feature/new", create=True)  # Create and switch to new branch
    """
    if not _is_git_repo(path):
        return f"Error: {path} is not a git repository"

    # Validate target reference
    is_valid, error_msg = _validate_git_ref(target)
    if not is_valid:
        return f"Error: Invalid target '{target}': {error_msg}"

    args = ["checkout"]
    if create:
        args.append("-b")
    args.extend(["--", target])  # Use -- to prevent option injection

    success, output = _run_git_command(args, cwd=path)
    return output if success else f"Error: {output}"


@mcp.tool()
def git_merge(
    branch: str,
    path: str = ".",
    no_ff: bool = False,
) -> str:
    """
    Merge a branch into the current branch.

    Args:
        branch: Branch to merge
        path: Repository path
        no_ff: Create a merge commit even for fast-forward merges

    Returns:
        Merge result or error message
    """
    if not _is_git_repo(path):
        return f"Error: {path} is not a git repository"

    # Validate branch reference
    is_valid, error_msg = _validate_git_ref(branch)
    if not is_valid:
        return f"Error: Invalid branch '{branch}': {error_msg}"

    args = ["merge"]
    if no_ff:
        args.append("--no-ff")
    args.append(branch)

    success, output = _run_git_command(args, cwd=path)
    return output if success else f"Error: {output}"


if __name__ == "__main__":
    mcp.run()
