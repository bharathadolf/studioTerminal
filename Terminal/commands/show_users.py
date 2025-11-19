
import os
import json
from typing import List
from rich.console import Console
from rich.table import Table
from ..utils.command_utils import validate_args

VALID_ARGS = ["-h", "--help"]

def show_users_help():
    """Displays help information for the show_users command."""
    console = Console()
    console.print("\n[bold]Usage: showuser[/bold]\n")
    console.print("Displays all existing users and their assigned roles.\n")
    table = Table(title="show_users Command Help", show_header=True, header_style="bold cyan")
    table.add_column("Argument", style="dim", width=20)
    table.add_column("Description")

    table.add_row("-h, --help", "Show this help message.")
    console.print(table)

def show_users_command(session, args: List[str]):
    """
    Shows all existing users and their assigned roles.
    This command is restricted by the shell to specific roles.
    """
    if validate_args(args, VALID_ARGS, show_users_help):
        return

    console = Console()

    # --- Data Fetching ---
    user_roles = {}
    roles_file_path = "Data/users_config.json"
    if os.path.exists(roles_file_path):
        with open(roles_file_path, "r") as f:
            try:
                user_roles = json.load(f)
            except json.JSONDecodeError:
                console.print(f"[bold red]Error: Could not parse {roles_file_path}.[/bold red]")
                return

    users_dir = "Data/roles"
    if not os.path.exists(users_dir) or not os.path.isdir(users_dir):
        console.print("[yellow]No user data directory found. No users to show.[/yellow]")
        return

    try:
        user_ids = [d for d in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, d))]
    except OSError as e:
        console.print(f"[bold red]Error reading user directory {users_dir}: {e}[/bold red]")
        return

    # --- Display ---
    table = Table(title="[bold]All System Users[/bold]")
    table.add_column("User ID", style="cyan", no_wrap=True)
    table.add_column("Assigned Role", style="green")

    if not user_ids:
        console.print("[yellow]No users found.[/yellow]")
        return

    for user_id in sorted(user_ids):
        role = user_roles.get(user_id, "N/A")
        table.add_row(user_id, role)

    console.print(table)

def register_commands(registry):
    registry.register("showuser", show_users_command)
