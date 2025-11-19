from rich.console import Console
from typing import List, Callable

def validate_args(args: List[str], valid_args: List[str], help_function: Callable[[], None]) -> bool:
    """
    Validates command-line arguments against a list of valid flags.

    This function performs two main checks:
    1. If a standard help flag ('-h' or '--help') is present, it calls the
       provided help function and signals to stop execution.
    2. It identifies any provided flags (arguments starting with '-') that are not
       in the valid_args list. If any are found, it prints an error message
       for each, calls the help function, and signals to stop execution.

    Args:
        args: A list of arguments passed to the command.
        valid_args: A list of valid argument flags (e.g., ['--user', '--role']).
        help_function: A zero-argument function that prints help/usage info.
"""
    console = Console()
    if any(arg in ['-h', '--help'] for arg in args):
        help_function()
        return True

    invalid_flags = [arg for arg in args if arg.startswith('-') and arg not in valid_args]
    if invalid_flags:
        for flag in invalid_flags:
            console.print(f"[red]Error: Unknown flag '{flag}'[/red]")
        help_function()
        return True

    return False
