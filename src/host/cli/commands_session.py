"""
Session Management CLI Commands Handler

Handles session commands: sessions, resume, rename, export, fork, checkpoints, rewind, tasks, task
"""

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.host.cli.command_context import CommandContext
from src.host.cli.command_result import CommandResult

console = Console()


class SessionCommandHandler:
    """Handle session management slash commands in the CLI."""

    def __init__(self, cc: CommandContext):
        self.cc = cc

    def __getattr__(self, name):
        """Proxy attribute access to the underlying CommandContext."""
        return getattr(self.cc, name)

    async def handle_session_command(
        self,
        cmd: str,
        cmd_args: list[str],
    ) -> CommandResult | None:
        """Handle session management commands."""
        handlers = {
            "sessions": self._show_sessions,
            "resume": lambda: self._resume_session(cmd_args),
            "rename": lambda: self._rename_session(cmd_args),
            "export": lambda: self._export_session(cmd_args),
            "fork": self._fork_session,
            "checkpoints": self._show_checkpoints,
            "rewind": lambda: self._rewind_checkpoint(cmd_args),
            "tasks": self._show_tasks,
            "task": lambda: self._show_task_output(cmd_args),
            "ralph": lambda: self._handle_ralph(cmd_args),
        }
        handler = handlers.get(cmd)
        if handler is None:
            return None
        result = handler()
        return result if isinstance(result, CommandResult) else CommandResult()

    def _show_sessions(self):
        """List recent sessions."""
        sessions = self.session_mgr.list_sessions(project=self.project, limit=10)
        if sessions:
            table = Table(title="Recent Sessions")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Messages", style="yellow")
            table.add_column("Updated")
            for s in sessions:
                updated = datetime.fromtimestamp(s.updated_at).strftime("%Y-%m-%d %H:%M")
                table.add_row(s.id[:8], s.name or "-", str(s.message_count), updated)
            console.print(table)
        else:
            console.print("[dim]No sessions found[/dim]")

    def _resume_session(self, cmd_args: list):
        """Resume a session."""
        if cmd_args:
            session_data = self.session_mgr.resume_session(cmd_args[0])
            if session_data:
                console.print(f"[green]Resumed: {session_data.metadata.get_display_name()}[/green]")
            else:
                console.print(f"[red]Session not found: {cmd_args[0]}[/red]")
        else:
            console.print("[yellow]Usage: /resume <session_id or name>[/yellow]")

    def _rename_session(self, cmd_args: list):
        """Rename current session."""
        if cmd_args:
            new_name = " ".join(cmd_args)
            self.session_mgr.rename_session(self.ctx.session_id, new_name)
            console.print(f"[green]Session renamed to: {new_name}[/green]")
        else:
            console.print("[yellow]Usage: /rename <new_name>[/yellow]")

    def _export_session(self, cmd_args: list):
        """Export session."""
        try:
            path = cmd_args[0] if cmd_args else f"session_{self.ctx.session_id[:8]}.md"
            self.session_mgr.export_session(self.ctx.session_id, format="markdown", path=path)
            console.print(f"[green]Exported to: {path}[/green]")
        except Exception as e:
            console.print(f"[red]Export failed: {e}[/red]")

    def _fork_session(self):
        """Fork current session."""
        try:
            forked = self.session_mgr.fork_session(self.ctx.session_id)
            if forked:
                console.print(f"[green]Forked session: {forked.metadata.id}[/green]")
            else:
                console.print("[red]Fork failed[/red]")
        except Exception as e:
            console.print(f"[red]Fork failed: {e}[/red]")

    def _show_checkpoints(self):
        """List checkpoints."""
        cps = self.checkpoint_mgr.list_checkpoints(limit=10)
        if cps:
            table = Table(title="Checkpoints")
            table.add_column("ID", style="cyan")
            table.add_column("Time", style="green")
            table.add_column("Files", style="yellow")
            table.add_column("Prompt")
            for cp in cps:
                table.add_row(
                    cp["id"][:8],
                    cp["created_at"].split("T")[1][:8],
                    str(cp["files_count"]),
                    cp["prompt"][:40] + "..." if len(cp["prompt"]) > 40 else cp["prompt"],
                )
            console.print(table)
        else:
            console.print("[dim]No checkpoints yet[/dim]")

    def _rewind_checkpoint(self, cmd_args: list):
        """Rewind to checkpoint."""
        try:
            if cmd_args:
                result = self.checkpoint_mgr.rewind(cmd_args[0], mode="code")
            else:
                result = self.checkpoint_mgr.rewind_last(mode="code")

            if result:
                console.print(f"[green]Rewound: {len(result['restored_files'])} files restored[/green]")
                if result["failed_files"]:
                    console.print(f"[yellow]Failed: {len(result['failed_files'])} files[/yellow]")
            else:
                console.print("[yellow]No checkpoint to rewind to[/yellow]")
        except Exception as e:
            console.print(f"[red]Rewind failed: {e}[/red]")

    def _show_tasks(self):
        """List background tasks."""
        tasks = self.task_mgr.list_tasks(limit=10)
        if tasks:
            table = Table(title="Background Tasks")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Progress")
            table.add_column("Duration")
            for t in tasks:
                status_color = {
                    "running": "cyan",
                    "completed": "green",
                    "failed": "red",
                    "cancelled": "yellow",
                }.get(t["status"], "white")
                table.add_row(
                    t["id"],
                    t["name"][:20],
                    f"[{status_color}]{t['status']}[/{status_color}]",
                    f"{t['progress']}%",
                    f"{t['duration'] or 0:.1f}s",
                )
            console.print(table)
        else:
            console.print("[dim]No tasks[/dim]")

    def _show_task_output(self, cmd_args: list):
        """Show task output."""
        if cmd_args:
            output = self.task_mgr.get_task_output(cmd_args[0])
            if output:
                console.print(Panel(output, title=f"Task {cmd_args[0]}", border_style="cyan"))
            else:
                console.print(f"[red]Task not found: {cmd_args[0]}[/red]")
        else:
            console.print("[yellow]Usage: /task <task_id>[/yellow]")

    def _handle_ralph(self, cmd_args: list):
        """Handle Ralph outer-loop commands."""
        if not self.ralph_mgr:
            console.print("[red]Ralph manager is not available[/red]")
            return None

        if not cmd_args:
            console.print(
                "[yellow]Usage: /ralph <init|add|list|active|next|run-next|resume-active|done|blocked> ...[/yellow]"
            )
            return None

        subcmd = cmd_args[0].lower()
        rest = cmd_args[1:]

        handlers = {
            "init": self._ralph_init,
            "add": self._ralph_add,
            "list": self._ralph_list,
            "active": self._ralph_active,
            "next": self._ralph_next,
            "run-next": self._ralph_run_next,
            "resume-active": self._ralph_resume_active,
            "done": self._ralph_done,
            "blocked": self._ralph_blocked,
        }
        handler = handlers.get(subcmd)
        if handler is None:
            console.print(f"[yellow]Unknown /ralph command: {subcmd}[/yellow]")
            return None
        return handler(rest)

    def _ralph_init(self, _args: list[str]):
        path = self.ralph_mgr.init_storage()
        console.print(f"[green]Initialized Ralph state:[/green] {path}")
        return None

    def _ralph_add(self, args: list[str]):
        if not args:
            console.print("[yellow]Usage: /ralph add <task title>[/yellow]")
            return None
        task = self.ralph_mgr.add_task(" ".join(args))
        console.print(f"[green]Added Ralph task[/green] {task.id}: {task.title}")
        return None

    def _ralph_list(self, _args: list[str]):
        tasks = self.ralph_mgr.list_tasks()
        if not tasks:
            console.print("[dim]No Ralph tasks[/dim]")
            return None

        table = Table(title="Ralph Tasks")
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Attempts", style="magenta")
        table.add_column("Title", style="green")
        for task in tasks:
            table.add_row(task.id, task.status, str(task.attempts), task.title)
        console.print(table)
        return None

    def _ralph_active(self, _args: list[str]):
        task = self.ralph_mgr.get_active_task()
        if task is None:
            console.print("[dim]No active Ralph task[/dim]")
            return None
        console.print(
            Panel(
                task.last_prompt or task.title,
                title=f"Ralph Active: {task.id}",
                border_style="cyan",
            )
        )
        return None

    def _ralph_next(self, _args: list[str]):
        task = self.ralph_mgr.choose_next_task()
        if task is None:
            console.print("[dim]No pending Ralph tasks[/dim]")
            return None
        console.print(Panel(task.last_prompt, title=f"Ralph Next: {task.id}", border_style="blue"))
        return None

    def _ralph_run_next(self, _args: list[str]):
        task = self.ralph_mgr.choose_next_task()
        if task is None:
            console.print("[dim]No pending Ralph tasks[/dim]")
            return CommandResult(next_prompt=None)

        self.ctx.reset()

        console.print(
            Panel(
                task.last_prompt,
                title=f"Ralph Run-Next: {task.id}",
                border_style="green",
            )
        )
        console.print("[dim]Starting fresh inner-agent run for selected Ralph task.[/dim]")
        return CommandResult(
            conversation_history=[],
            next_prompt=task.last_prompt,
        )

    def _ralph_resume_active(self, _args: list[str]):
        prompt = self.ralph_mgr.resume_active_prompt()
        if prompt is None:
            console.print("[dim]No active Ralph task[/dim]")
            return CommandResult(next_prompt=None)

        self.ctx.reset()
        active_task = self.ralph_mgr.get_active_task()
        title = active_task.id if active_task else "active"
        console.print(
            Panel(
                prompt,
                title=f"Ralph Resume: {title}",
                border_style="cyan",
            )
        )
        console.print("[dim]Resuming active Ralph task in a fresh inner-agent run.[/dim]")
        return CommandResult(
            conversation_history=[],
            next_prompt=prompt,
        )

    def _ralph_done(self, args: list[str]):
        if not args:
            console.print("[yellow]Usage: /ralph done <task_id> [note][/yellow]")
            return None
        task_id = args[0]
        note = " ".join(args[1:])
        if self.ralph_mgr.mark_done(task_id, note):
            console.print(f"[green]Marked Ralph task done:[/green] {task_id}")
        else:
            console.print(f"[red]Ralph task not found:[/red] {task_id}")
        return None

    def _ralph_blocked(self, args: list[str]):
        if len(args) < 2:
            console.print("[yellow]Usage: /ralph blocked <task_id> <reason>[/yellow]")
            return None
        task_id = args[0]
        reason = " ".join(args[1:])
        if self.ralph_mgr.mark_blocked(task_id, reason):
            console.print(f"[yellow]Marked Ralph task blocked:[/yellow] {task_id}")
        else:
            console.print(f"[red]Ralph task not found:[/red] {task_id}")
        return None
