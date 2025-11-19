
import os
import json
import inspect
from rich.console import Console
from rich.panel import Panel
from Terminal.core.state.session import Session
from Terminal.ui.banner import show_banner
from Terminal.core.system.startup import startup_manager
from Terminal.commands.userInfo import get_persistent_user_id
from Terminal.core.registries.command_registry import CommandRegistry
from Terminal.commands import register_all_commands
from Terminal.core.system.jobs import job_manager

from Terminal.utils.config_validation import validate_roles_config, validate_users_config

console = Console()
class TerminalShell:
    def __init__(self, root_dir=None):
        if root_dir is None:
            # Calculate root_dir relative to this file (Terminal/core/shell.py) -> Termina/
            self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        else:
            self.root_dir = root_dir

        self.session = Session(self.root_dir)
        self.session.user_id = get_persistent_user_id("sysinfo")
        self.roles = ['artist', 'pipe', 'rnd', 'supe', 'master']
        
        # Initialize Registry
        self.registry = CommandRegistry()
        register_all_commands(self.registry)
        
        data_dir = os.path.join(self.root_dir, 'Data')
        self.roles_config = self._load_config(os.path.join(data_dir, 'roles_config.json'), 'roles')
        self.session.roles_config = self.roles_config
        self.users_config = self._load_config(os.path.join(data_dir, 'users_config.json'), 'users')
        self.session.users_config = self.users_config

    def _load_config(self, config_path, config_type):
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                
                valid = True
                error = None
                
                if config_type == 'roles':
                    valid, error = validate_roles_config(data)
                elif config_type == 'users':
                    valid, error = validate_users_config(data, self.roles)
                
                if not valid:
                    console.print(f"[bold red]Config Validation Error in {config_path}: {error}[/bold red]")
                    console.print("[yellow]Loading empty configuration to prevent crash.[/yellow]")
                    return {}
                
                return data
            except json.JSONDecodeError:
                console.print(f"[bold red]Error: Could not parse {config_path}. Invalid JSON.[/bold red]")
                return {}
        return {}

    def run(self):
        """Main loop to run the terminal shell."""
        user_id = self.session.user_id
        self._ensure_user_directory_and_files(user_id)

        assigned_role = self.users_config.get(user_id, 'artist')
        self.session.set_role(assigned_role)
        
        # Set allowed commands for the current role in the registry
        if assigned_role in self.roles_config:
            allowed_cmds = self.roles_config[assigned_role].get('allowed_commands', [])
            self.registry.set_allowed_commands(allowed_cmds)
        else:
            # If role not in config or config is empty, allow all commands
            self.registry.set_allowed_commands(list(self.registry.commands.keys()))

        for command in startup_manager.startup_commands:
            sig = inspect.signature(command)
            if len(sig.parameters) > 0:
                command(self.session)
            else:
                command()

        show_banner()

        if assigned_role != 'master':
            console.print(f"Your assigned role is [bold cyan]{assigned_role}[/bold cyan]. You cannot switch roles.")
        else:
            console.print(f"You have the [bold gold]master[/bold gold] role. You can switch to any role.")

        keep_running = True
        while keep_running:
            try:
                prompt_text = self.session.get_prompt()
                user_input = self.session.prompt(prompt_text)

                if not user_input:
                    continue

                if user_input.lower() in self.roles:
                    user_id = self.session.user_id
                    assigned_role = self.users_config.get(user_id)
                    if assigned_role == 'master':
                        new_role = user_input.lower()
                        self.session.set_role(new_role)
                        
                        # Update allowed commands for the new role
                        if new_role in self.roles_config:
                            allowed_cmds = self.roles_config[new_role].get('allowed_commands', [])
                            self.registry.set_allowed_commands(allowed_cmds)
                        else:
                            self.registry.set_allowed_commands(list(self.registry.commands.keys()))
                        
                        console.print(f"Switched to [bold cyan]{self.session.current_role}[/bold cyan] role.")
                    else:
                        console.print("[red]You do not have permission to switch roles.[/red]")
                    continue
                
                # Handle Background Jobs
                run_in_background = False
                if user_input.strip().endswith('&'):
                    run_in_background = True
                    user_input = user_input.strip()[:-1].strip()

                import shlex
                try:
                    parts = shlex.split(user_input)
                except ValueError as e:
                    console.print(f"[red]Error parsing command: {e}[/red]")
                    continue
                
                if not parts:
                    continue

                command_name = parts[0].lower()
                args = parts[1:]

                if command_name == 'jobs':
                    job_manager.list_jobs()
                    continue

                command_func = self.registry.get_command(command_name)

                if command_func:
                    if self.session.current_role == 'rnd':
                        func = command_func
                        docstring = inspect.getdoc(func)
                        source_file = inspect.getsourcefile(func)
                        line_number = inspect.getsourcelines(func)[1]

                        panel_content = f"[bold]Function:[/bold] {func.__module__}.{func.__name__}\n"
                        panel_content += f"[bold]File:[/bold] [green]{source_file}[/green]:[yellow]{line_number}[/yellow]\n"
                        panel_content += f"[bold]Arguments:[/bold] {args}\n\n"
                        panel_content += f"[bold]Docstring:[/bold]\n{docstring}"

                        console.print(Panel(panel_content, title="R&D Function Call Details", expand=False))

                    if self._is_authorized(command_name):
                        if run_in_background:
                            job_manager.submit_job(command_func, args, self.session, command_name)
                        else:
                            if command_name == 'exit':
                                keep_running = command_func()
                            elif command_name == 'quit':
                                command_func(self.session, args)
                            else:
                                command_func(self.session, args)
                    else:
                        console.print(f"[red]Error: You do not have permission to use the '{command_name}' command.[/red]")
                else:
                    console.print(f"[red]Command not found: {command_name}[/red]")

            except KeyboardInterrupt:
                console.print("", end="")
                continue
            except EOFError:
                keep_running = False
            except Exception as e:
                console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")

        console.print("\nExiting terminal. Goodbye!")

    def _ensure_user_directory_and_files(self, user_id):
        user_dir = os.path.join(self.root_dir, "Data", "roles", user_id)
        os.makedirs(user_dir, exist_ok=True)

        for ext in ["html", "json", "txt"]:
            file_path = os.path.join(user_dir, f"{user_id}.{ext}")
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    pass

    def _is_authorized(self, command_name):
        """Check if the current user role is authorized to run the command."""
        user_id = self.session.user_id
        assigned_role = self.users_config.get(user_id)
        
        if assigned_role == 'master':
            return True

        if not self.roles_config:
            return True
        
        current_permissions = self.roles_config.get(self.session.current_role, {})
        allowed_commands = current_permissions.get('allowed_commands', [])

        if command_name in allowed_commands:
            return True
        return False
