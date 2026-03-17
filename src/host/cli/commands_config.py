"""
Configuration CLI Commands Handler

Handles configuration commands: model, doctor, workspace, add-dir
"""

from pathlib import Path

from rich.console import Console

from src.core.doctor import Doctor
from src.core.model_manager import ModelManager
from src.core.workspace import WorkspaceManager
from src.host.cli.command_context import CommandContext
from src.host.cli.command_result import CommandResult

console = Console()


class ConfigCommandHandler:
    """Handle configuration slash commands in the CLI."""

    def __init__(self, cc: CommandContext):
        self.cc = cc

    def __getattr__(self, name):
        """Proxy attribute access to the underlying command context."""
        return getattr(self.cc, name)

    async def handle(
        self,
        cmd: str,
        cmd_args: list[str],
        mode: str | None = None,
        tool_names: list[str] | None = None,
        tool_definitions: list | None = None,
        conversation_history: list | None = None,
        active_skills_content: str | None = None,
    ) -> CommandResult | None:
        """Handle configuration commands."""
        handlers = {
            "model": lambda: self._handle_model(cmd_args),
            "doctor": self._run_doctor,
            "workspace": self._show_workspace,
            "add-dir": lambda: self._add_directory(cmd_args),
        }
        handler = handlers.get(cmd)
        if handler is None:
            return None
        handler()
        return CommandResult()

    def _handle_model(self, cmd_args: list):
        """Handle model switching."""
        model_mgr = ModelManager(default_model=self.model_name)
        if cmd_args:
            new_model = cmd_args[0]
            if model_mgr.switch_model(new_model):
                self.model_name = model_mgr.get_current_model()
                console.print(f"[green]Switched to model: {self.model_name}[/green]")
            else:
                console.print(f"[red]Unknown model: {new_model}[/red]")
                console.print(model_mgr.format_model_list())
        else:
            console.print(model_mgr.format_model_list())

    def _run_doctor(self):
        """Run health checks."""
        doctor = Doctor(project_dir=Path.cwd())
        console.print("[bold]Running health checks...[/bold]")
        results = doctor.run_all_checks()
        console.print(doctor.format_results(results))

    def _show_workspace(self):
        """Show workspace directories."""
        workspace_mgr = WorkspaceManager(primary_dir=Path.cwd())
        console.print("[bold]Workspace Directories:[/bold]")
        console.print(workspace_mgr.get_summary())

    def _add_directory(self, cmd_args: list):
        """Add a directory to workspace."""
        workspace_mgr = WorkspaceManager(primary_dir=Path.cwd())
        if cmd_args:
            dir_path = cmd_args[0]
            alias = cmd_args[1] if len(cmd_args) > 1 else None
            if workspace_mgr.add_directory(dir_path, alias=alias):
                console.print(f"[green]Added: {dir_path}[/green]")
            else:
                console.print(f"[red]Failed to add: {dir_path}[/red]")
        else:
            console.print("[yellow]Usage: /add-dir <path> [alias][/yellow]")
