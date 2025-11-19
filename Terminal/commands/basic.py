import os
import json
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from Terminal.utils.command_utils import validate_args
from Terminal.ui.banner import show_banner

console = Console()

COMMANDS = {
    'help': {'desc': 'Displays all the available commands.', 'usage': 'help'},
    'll': {'desc': 'Displays the current location where the terminal is launched.', 'usage': 'll'},
    'ls': {'desc': 'Displays all the files in the current directory.', 'usage': 'ls'},
    'cd': {'desc': 'Changes into the specified directory.', 'usage': 'cd <directory>'},
    'dir': {'desc': 'Displays all the subfolders in the current directory.', 'usage': 'dir'},
    'pwd': {'desc': 'Prints the current working directory.', 'usage': 'pwd'},
    'clear': {'desc': 'Clears the terminal screen.', 'usage': 'clear'},
    'run': {'desc': 'Runs a program or script. Use -h for details.', 'usage': 'run <program> [args...]'},
    'userinfo': {'desc': 'Displays detailed user and system information. Use --export [html|json|txt] --output <path> to export.', 'usage': 'userinfo'},
    'showuser': {'desc': 'Shows all existing users and their assigned roles.', 'usage': 'showuser'},
    'assign': {'desc': 'Assigns roles or modifies role permissions. Use -h for details.', 'usage': 'assign <user_id> [options]'},
    'exit': {'desc': 'Exits the terminal.', 'usage': 'exit'},
    'quit': {'desc': 'Quits background processes. Use -h for details.', 'usage': 'quit [--all]'},
    'dcc': {'desc': 'Lists DCC apps. Use --export [PATH] to export paths to a YAML file.', 'usage': 'dcc [--export [PATH]]'},
}

def help_command(session, args):
    current_role = session.current_role
    roles_config = session.roles_config

    table = Table(title=f"Available Commands for Role: [bold cyan]{current_role}[/bold cyan]")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="magenta")
    table.add_column("Usage", justify="right", style="green")

    if current_role == 'master':
        for cmd, data in COMMANDS.items():
            table.add_row(cmd, data['desc'], data['usage'])
    else:
        role_permissions = roles_config.get(current_role, {})
        allowed_commands = role_permissions.get('allowed_commands', [])
        for cmd in allowed_commands:
            if cmd in COMMANDS:
                data = COMMANDS[cmd]
                table.add_row(cmd, data['desc'], data['usage'])

    console.print(table)

def ll_command(session, args):
    console.print(os.getcwd())

def ls_command(session, args):
    for item in os.listdir():
        console.print(item)

def cd_command(session, args):
    if not args:
        console.print("[red]Error: Please specify a directory.[/red]")
        return
    try:
        os.chdir(args[0])
    except FileNotFoundError:
        console.print(f"[red]Error: Directory not found: {args[0]}[/red]")
    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")

def dir_command(session, args):
    try:
        subfolders = [f.name for f in os.scandir() if f.is_dir()]
        if not subfolders:
            console.print("No subfolders found.")
        else:
            for folder in subfolders:
                console.print(folder)
    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")

def pwd_command(session, args):
    """Prints the current working directory."""
    console.print(os.getcwd())

def clear_command(session, args):
    os.system("cls" if os.name == "nt" else "clear")
    show_banner()


def _run_help():
    """Displays detailed help for the 'run' command."""
    help_text = """
    [bold]NAME[/bold]
        run - Executes a program or script in a new background process.

    [bold]SYNOPSIS[/bold]
        [bold]run[/bold] <command> [argument...]
        [bold]run[/bold] [|-h|--help|]

    [bold]DESCRIPTION[/bold]
        The `run` command launches a new background process to execute a specified
        program or script. The terminal finds the executable by searching the
        directories listed in the system's `PATH` environment variable.

        This allows you to continue using the terminal while the program runs
        in the background. Any processes started this way are tracked by the
        current terminal session.

    [bold]EXAMPLES[/bold]
        - To run a Python script:
          `run python my_script.py`

        - To list files in a directory with `ls`:
          `run ls -l /path/to/dir`

    [bold]PROCESS MANAGEMENT[/bold]
        - Use the `quit` command to terminate the last process started by `run`.
        - Use `quit --all` to terminate all background processes from the session.
    """
    console.print(Panel(help_text, title="run Command Help", expand=False, border_style="green"))

def run_command(session, args):
    """Runs a program or script in the background."""
    if validate_args(args, [], _run_help):
        return

    if not args:
        _run_help()
        return

    try:
        process = subprocess.Popen(args)
        session.processes.append(process)
        console.print(f"Started process {process.pid}: {' '.join(args)}")
    except FileNotFoundError:
        console.print(f"[red]Error: Command '{args[0]}' not found.[/red]")
        console.print("Ensure the program is in your system's PATH or provide the full path.")
    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")

def exit_command():
    return False

def _quit_help():
    """Displays detailed help for the 'quit' command."""
    help_text = """
    [bold]NAME[/bold]
        quit - Terminates background processes launched by the `run` command.

    [bold]SYNOPSIS[/bold]
        [bold]quit[/bold] [--all]
        [bold]quit[/bold] [|-h|--help|]

    [bold]DESCRIPTION[/bold]
        The `quit` command is used to terminate background processes that were
        started with the `run` command.

        By default, without any flags, `quit` will terminate the most recent
        background process that was started.

    [bold]OPTIONS[/bold]
        [bold]--all[/bold]
            Terminates all background processes currently managed by the terminal session.

    [bold]EXAMPLES[/bold]
        - To quit the last process you started:
          `quit`

        - To quit all running background processes:
          `quit --all`
    """
    console.print(Panel(help_text, title="quit Command Help", expand=False, border_style="green"))

def quit_command(session, args):
    """Quits running processes."""
    if validate_args(args, ['--all'], _quit_help):
        return

    if not session.processes:
        console.print("[yellow]No running processes to quit.[/yellow]")
        return

    if "--all" in args:
        for p in session.processes:
            p.terminate()
        session.processes.clear()
        console.print("[bold green]All processes terminated.[/bold green]")
    elif not args:
        process_to_quit = session.processes.pop()
        process_to_quit.terminate()
        console.print(f"[bold green]Process {process_to_quit.pid} terminated.[/bold green]")
    else:
        _quit_help()

def register_commands(registry):
    registry.register("help", help_command)
    registry.register("ll", ll_command)
    registry.register("ls", ls_command)
    registry.register("cd", cd_command)
    registry.register("dir", dir_command)
    registry.register("pwd", pwd_command)
    registry.register("clear", clear_command)
    registry.register("run", run_command)
    registry.register("exit", exit_command)
    registry.register("quit", quit_command)
