from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def show_banner():
    """Displays the welcome banner for the terminal."""
    banner_text = Text("🎬  BURRA PAADU VFX STUDIO - CORE SHELL  🎬", justify="center", style="bold magenta")
    panel = Panel(
        banner_text,
        border_style="green",
    )
    console.print(panel)
    console.print("Welcome to the Studio Terminal!", style="green", justify="center")
    console.print("Type 'help' for available commands or 'exit' to quit.\n", justify="center")
