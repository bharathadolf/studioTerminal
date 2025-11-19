
import os
import json
from rich.console import Console
from rich.table import Table
from ..utils.config_validation import validate_roles_config, validate_users_config

from ..utils.command_utils import validate_args
from ..commands.basic import COMMANDS
from typing import List

console = Console()

VALID_ARGS = ["--role", "-h", "--help", "--category", "--add-command", "--remove-command"]
ROLES_DIR = "data/roles"
# In-memory representation of command categories and hierarchy
COMMAND_CATEGORIES = {
    'help': 'base', 'll': 'base', 'clear': 'base', 'userinfo': 'base',
    'showuser': 'base', 'exit': 'base', 'quit': 'base',
    'ls': 'artist', 'cd': 'artist', 'dir': 'artist', 'pwd': 'artist',
    'run': 'rnd',
    'assign': 'master'
}
HIERARCHY_ORDER = ['base', 'artist', 'supe', 'pipe', 'rnd', 'master']

def _show_help():
    """Displays comprehensive help for the assign command in structured tables."""
    console.print("\n[bold]assign Command Help[/bold]\n")

    # Usage Table
    usage_table = Table(title="Command Usage", show_header=True, header_style="bold magenta")
    usage_table.add_column("Pattern", style="cyan", no_wrap=True)
    usage_table.add_column("Description")
    
    usage_table.add_row("assign <user_id> --role <role_name>", "Assigns a primary role to a user.")
    usage_table.add_row("assign <user_id> --category <parent_role> --role <new_role>", "Creates a sub-role under a parent and assigns it to the user.")
    usage_table.add_row("assign --role <role_name> --add-command <cmd1> [cmd2]...", "Adds one or more commands to a role.")
    usage_table.add_row("assign --role <role_name> --remove-command <cmd1> [cmd2]...", "Removes one or more commands from a role.")
    usage_table.add_row("assign <user_id> --add-command <cmd1> [cmd2]...", "Adds one or more commands specifically for a user.")
    usage_table.add_row("assign <user_id> --remove-command <cmd1> [cmd2]...", "Removes one or more user-specific commands.")
    usage_table.add_row("assign --help or -h", "Displays this detailed help guide.")
    
    console.print(usage_table)

    # Examples Table
    examples_table = Table(title="Examples", show_header=True, header_style="bold magenta")
    examples_table.add_column("Command", style="cyan", no_wrap=True)
    examples_table.add_column("What Happens")

    examples_table.add_row("assign 4d8d28d3 --role artist", "The user '4d8d28d3' is assigned the 'artist' role.")
    examples_table.add_row("assign 4d8d28d3 --category artist --role 3d_modeler", "A new role '3d_modeler' is created under 'artist', and then assigned to user '4d8d28d3'.")
    examples_table.add_row("assign --role artist --add-command ls", "The 'ls' command is added to the list of commands allowed for the 'artist' role.")
    examples_table.add_row("assign --role artist --remove-command ls", "The 'ls' command is removed from the 'artist' role.")
    examples_table.add_row("assign 4d8d28d3 --add-command ll cd", "Adds 'll' and 'cd' to a special list of commands just for user '4d8d28d3'. These are in addition to their role commands.")
    examples_table.add_row("assign 4d8d28d3 --remove-command ll", "Removes 'll' from the user-specific command list for '4d8d28d3'.")
    
    console.print(examples_table)

    # Role Hierarchy Table
    hierarchy_table = Table(title="Role Hierarchy Rules", show_header=True, header_style="bold magenta")
    hierarchy_table.add_column("Role", style="cyan")
    hierarchy_table.add_column("Can Create Sub-roles Under")
    
    hierarchy_table.add_row("master", "'master', 'supe', 'pipe', 'rnd', and 'artist' roles.")
    hierarchy_table.add_row("rnd", "'pipe'")
    hierarchy_table.add_row("pipe", "'supe'")
    hierarchy_table.add_row("supe", "'artist'")
    
    console.print(hierarchy_table)

def assign_command(session, args: List[str]):
    """Main function to handle the 'assign' command logic."""
    if not args or '--help' in args or '-h' in args:
        _show_help()
        return

    is_role_modification = "--role" in args and ("--add-command" in args or "--remove-command" in args)
    is_user_modification = not is_role_modification and len(args) > 0 and not args[0].startswith('--')

    if is_role_modification:
        _handle_role_command_modification(args)
    elif is_user_modification:
        user_id = args[0]
        if "--add-command" in args or "--remove-command" in args:
            _handle_user_command_modification(user_id, args[1:])
        elif "--role" in args:
             _assign_user_role(user_id, args[args.index("--role") + 1])
        elif "--category" in args:
            console.print("[yellow]Sub-role creation logic needs to be fully implemented.[/yellow]")
        else:
            _show_help()
    else:
        _show_help()

def _handle_role_command_modification(args: List[str]):
    """Handles adding/removing commands for a role."""
    try:
        role_index = args.index("--role") + 1
        role_name = args[role_index]
        
        commands_to_add = _get_commands_from_args(args, "--add-command")
        commands_to_remove = _get_commands_from_args(args, "--remove-command")

        if commands_to_add:
            _modify_role_commands(role_name, commands_to_add, "add")
        if commands_to_remove:
            _modify_role_commands(role_name, commands_to_remove, "remove")

    except (ValueError, IndexError):
        console.print("[red]Error: Invalid syntax for role command modification.[/red]")
        _show_help()

def _handle_user_command_modification(user_id: str, args: List[str]):
    """Handles adding/removing commands for a user."""
    commands_to_add = _get_commands_from_args(args, "--add-command")
    commands_to_remove = _get_commands_from_args(args, "--remove-command")

    if commands_to_add:
        _modify_user_commands(user_id, add_commands=commands_to_add)
    if commands_to_remove:
        _modify_user_commands(user_id, remove_commands=commands_to_remove)

def _get_commands_from_args(args: List[str], flag: str) -> List[str]:
    """Extracts a list of commands following a specific flag."""
    commands = []
    if flag in args:
        try:
            start_index = args.index(flag) + 1
            for arg in args[start_index:]:
                if arg.startswith('--'):
                    break
                commands.append(arg)
        except IndexError:
            pass
    return commands

def _modify_role_commands(role_name: str, commands: List[str], action: str):
    roles_config_path = "Data/roles_config.json"
    roles_config = _load_json_file(roles_config_path)

    if role_name not in roles_config and role_name not in HIERARCHY_ORDER:
        console.print(f"[bold red]Error: Role '{role_name}' does not exist.[/bold red]")
        return

    for command in commands:
        if command not in COMMANDS:
            console.print(f"[bold red]Error: Command '{command}' is not a valid command.[/bold red]")
            continue

        if action == "add":
            target_role_base = _get_base_role(role_name, roles_config)
            command_category = COMMAND_CATEGORIES.get(command, "base")

            target_level = HIERARCHY_ORDER.index(target_role_base)
            command_level = HIERARCHY_ORDER.index(command_category)

            if target_level < command_level:
                console.print(f"[bold red]Error: Cannot assign command '{command}' to role '{role_name}'.[/bold red]")
                continue
                
        if "allowed_commands" not in roles_config.get(role_name, {}):
            roles_config[role_name] = roles_config.get(role_name, {})
            roles_config[role_name]["allowed_commands"] = []

        allowed_commands = roles_config[role_name]["allowed_commands"]

        if action == "add":
            if command not in allowed_commands:
                allowed_commands.append(command)
                console.print(f"Successfully added command '[bold green]{command}[/bold green]' to role '[bold cyan]{role_name}[/bold cyan]'.")
        elif action == "remove":
            if command in allowed_commands:
                allowed_commands.remove(command)
                console.print(f"Successfully removed command '[bold green]{command}[/bold green]' from role '[bold cyan]{role_name}[/bold cyan]'.")

    _write_json_file(roles_config_path, roles_config)

def _modify_user_commands(user_id: str, add_commands: list = [], remove_commands: list = []):
    """Adds or removes commands from a user-specific config."""
    user_dir = os.path.join(ROLES_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    user_file = os.path.join(user_dir, "user_commands.json")

    if not os.path.exists(user_file):
        with open(user_file, 'w') as f:
            json.dump({"commands": []}, f, indent=4)

    with open(user_file, 'r+') as f:
        data = json.load(f)
        current_commands = data.get("commands", [])

        for cmd in add_commands:
            if cmd not in current_commands:
                current_commands.append(cmd)
                console.print(f"Command '{cmd}' added for user '{user_id}'.")
        
        for cmd in remove_commands:
            if cmd in current_commands:
                current_commands.remove(cmd)
                console.print(f"Command '{cmd}' removed for user '{user_id}'.")

        data["commands"] = current_commands
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

def _assign_user_role(user_id: str, role_name: str):
    users_config_path = "Data/users_config.json"
    users_config = _load_json_file(users_config_path)
    users_config[user_id] = role_name
    _write_json_file(users_config_path, users_config)
    console.print(f"Successfully assigned role '[bold cyan]{role_name}[/bold cyan]' to user '[bold yellow]{user_id}[/bold yellow]'.")

def _get_base_role(role_name: str, roles_config: dict) -> str:
    current = role_name
    while current in roles_config and "inherits_from" in roles_config[current]:
        parent = roles_config[current]["inherits_from"]
        if parent == current: # Break self-referential loops
            return "base" 
        current = parent
    return current if current in HIERARCHY_ORDER else "base"

def _load_json_file(file_path: str) -> dict:
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def _write_json_file(file_path: str, data: dict):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except IOError as e:
        console.print(f"[bold red]Error writing to {file_path}: {e}[/bold red]")

def register_commands(registry):
    registry.register("assign", assign_command)
