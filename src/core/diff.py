"""
Diff Visualization

Provides unified diff generation and visualization for file changes.
Supports inline diff, side-by-side comparison, and syntax highlighting.
"""

import difflib
import os
from dataclasses import dataclass

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()


@dataclass
class DiffHunk:
    """A single diff hunk."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[tuple[str, str]]  # (type, content) where type is ' ', '-', '+'


@dataclass
class DiffResult:
    """Result of a diff operation."""

    file_path: str
    hunks: list[DiffHunk]
    old_content: str | None
    new_content: str
    is_new_file: bool
    stats: dict[str, int]


def generate_diff(file_path: str, new_content: str) -> str:
    """
    Generate a colored diff between existing file content and new content.
    """
    # Handle new file case
    if not os.path.exists(file_path):
        return f"[new file] {file_path}\n" + new_content

    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            old_content = f.read()
    except Exception:
        return "[Binary or unreadable file - Cannot show diff]"

    diff_lines = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm="",
    )

    diff_text = "".join(diff_lines)
    if not diff_text:
        return "[No changes]"

    return diff_text


def compute_diff_result(file_path: str, new_content: str) -> DiffResult:
    """
    Compute a structured diff result with hunks and statistics.
    """
    is_new_file = not os.path.exists(file_path)
    old_content = None

    if not is_new_file:
        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                old_content = f.read()
        except Exception:
            is_new_file = True

    old_lines = old_content.splitlines() if old_content else []
    new_lines = new_content.splitlines()

    hunks = []
    stats = {"added": 0, "removed": 0, "changed": 0}

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        old_chunk = old_lines[i1:i2]
        new_chunk = new_lines[j1:j2]

        hunk_lines = []
        for line in old_chunk:
            hunk_lines.append(("-", line))
            stats["removed"] += 1
        for line in new_chunk:
            hunk_lines.append(("+", line))
            stats["added"] += 1

        if old_chunk and new_chunk:
            stats["changed"] += min(len(old_chunk), len(new_chunk))

        hunks.append(
            DiffHunk(
                old_start=i1 + 1,
                old_count=len(old_chunk),
                new_start=j1 + 1,
                new_count=len(new_chunk),
                lines=hunk_lines,
            )
        )

    return DiffResult(
        file_path=file_path,
        hunks=hunks,
        old_content=old_content,
        new_content=new_content,
        is_new_file=is_new_file,
        stats=stats,
    )


def print_diff(file_path: str, new_content: str):
    """
    Print a syntax-highlighted diff to the console.
    """
    diff_text = generate_diff(file_path, new_content)

    if diff_text.startswith("["):
        console.print(f"[yellow]{diff_text}[/yellow]")
    else:
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"Diff: {file_path}", expand=False))


def print_inline_diff(file_path: str, new_content: str, context_lines: int = 3):
    """
    Print an inline diff with line numbers and context.

    Shows only the changed lines with surrounding context.
    """
    result = compute_diff_result(file_path, new_content)

    if result.is_new_file:
        console.print(f"[green]✨ New file: {file_path}[/green]")
        syntax = Syntax(new_content, _detect_language(file_path), theme="monokai")
        console.print(Panel(syntax, title=f"[green]New File[/green]", expand=False))
        return

    if not result.hunks:
        console.print(f"[dim]No changes in {file_path}[/dim]")
        return

    stats_text = f"[green]+{result.stats['added']}[/green] [red]-{result.stats['removed']}[/red]"
    console.print(f"\n[bold cyan]📝 {file_path}[/bold cyan] {stats_text}")

    old_lines = result.old_content.splitlines() if result.old_content else []
    new_lines = new_content.splitlines()

    for hunk in result.hunks:
        console.print(
            f"\n[dim]@@ -{hunk.old_start},{hunk.old_count} "
            f"+{hunk.new_start},{hunk.new_count} @@[/dim]"
        )

        for change_type, line in hunk.lines:
            if change_type == "-":
                console.print(f"[red]  - {line}[/red]")
            elif change_type == "+":
                console.print(f"[green]  + {line}[/green]")


def print_side_by_side_diff(file_path: str, new_content: str):
    """
    Print a side-by-side diff comparison.
    """
    result = compute_diff_result(file_path, new_content)

    if result.is_new_file:
        console.print(f"[green]✨ New file: {file_path}[/green]")
        print_diff(file_path, new_content)
        return

    if not result.hunks:
        console.print(f"[dim]No changes in {file_path}[/dim]")
        return

    old_lines = result.old_content.splitlines() if result.old_content else []
    new_lines = new_content.splitlines()

    for hunk in result.hunks:
        table = Table(show_header=True, header_style="bold", expand=True)
        table.add_column("Line", style="dim", width=5)
        table.add_column("Original", style="red")
        table.add_column("Line", style="dim", width=5)
        table.add_column("Modified", style="green")

        old_idx = hunk.old_start - 1
        new_idx = hunk.new_start - 1

        for change_type, line in hunk.lines:
            if change_type == "-":
                table.add_row(
                    str(old_idx + 1),
                    Text(line, style="red"),
                    "",
                    "",
                )
                old_idx += 1
            elif change_type == "+":
                table.add_row(
                    "",
                    "",
                    str(new_idx + 1),
                    Text(line, style="green"),
                )
                new_idx += 1

        console.print(table)


def _detect_language(file_path: str) -> str:
    """Detect language from file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".lua": "lua",
        ".pl": "perl",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".less": "less",
        ".sql": "sql",
        ".md": "markdown",
        ".rst": "rst",
        ".txt": "text",
    }
    ext = os.path.splitext(file_path)[1].lower()
    return ext_map.get(ext, "text")
