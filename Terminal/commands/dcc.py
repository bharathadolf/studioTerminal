
import os
import yaml
import glob
from functools import lru_cache
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

DCC_APPS = {
    "maya": ["maya.exe"],
    "houdini": ["houdini.exe"],
    "nuke": ["Nuke.exe"],
    "blender": ["blender.exe", "blender-launcher.exe"],
    "substance_painter": ["Substance 3D Painter.exe"],
    "mari": ["Mari.exe", "Mari7.0v2.exe"],
    "marmoset": ["Marmoset Toolbag.exe", "toolbag.exe"],
}

@lru_cache(maxsize=None)
def scan_for_dcc_apps(search_paths: tuple[str]) -> list[dict]:
    """Scans for DCC applications in the specified search paths."""
    found_apps = []
    
    # Create a mapping of executable names to app names for faster lookup
    exe_to_app = {}
    for app_name, exe_names in DCC_APPS.items():
        for exe_name in exe_names:
            exe_to_app[exe_name] = app_name
    
    # Predefined specific paths for common DCC applications
    specific_paths = [
        # Blender paths
        r"C:\Program Files\Blender Foundation\Blender *\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender *\blender-launcher.exe",
        # Maya paths
        r"C:\Program Files\Autodesk\Maya*\bin\maya.exe",
        # Houdini paths
        r"C:\Program Files\Side Effects Software\Houdini *\bin\houdini.exe",
        # Mari paths
        r"C:\Program Files\Mari*\Bundle\bin\Mari*.exe",
        # Marmoset Toolbag paths
        r"C:\Program Files\Marmoset\Toolbag *\toolbag.exe",
        # Katana paths
        r"C:\Program Files\Katana*\bin\katanaBin.exe",
        # Gaea paths
        r"C:\Program Files\QuadSpinner\Gaea\Gaea.exe",
    ]
    
    # Check specific known paths first
    for path_pattern in specific_paths:
        if "*" in path_pattern:
            base_dir = os.path.dirname(path_pattern.replace("*", ""))
            if os.path.exists(base_dir):
                try:
                    version_dirs = os.listdir(base_dir)
                    for version_dir in version_dirs:
                        # Simple replacement for the first wildcard
                        full_path = path_pattern.replace("*", version_dir, 1)
                        
                        # Handle cases where there might be a second wildcard (like Mari*.exe)
                        if "*" in full_path:
                             matches = glob.glob(full_path)
                             for match in matches:
                                 if os.path.exists(match):
                                     _add_app_if_valid(match, found_apps)
                        else:
                            if os.path.exists(full_path):
                                _add_app_if_valid(full_path, found_apps)

                except (OSError, PermissionError):
                    pass
        else:
            if os.path.exists(path_pattern):
                exe_name = os.path.basename(path_pattern)
                if exe_name in exe_to_app:
                    app_name = exe_to_app[exe_name]
                    found_apps.append({
                        "name": app_name.replace("_", " ").title(),
                        "path": path_pattern
                    })
    
    # Also check the original search paths for any remaining apps
    for app_name, exe_names in DCC_APPS.items():
        for exe_name in exe_names:
            app_found = False
            # Check if already found in specific paths
            for found_app in found_apps:
                if os.path.basename(found_app["path"]) == exe_name:
                    app_found = True
                    break
            
            if not app_found:
                for search_path in search_paths:
                    if not os.path.exists(search_path):
                        continue
                    # Only check immediate subdirectories for known app patterns
                    try:
                        if os.path.isdir(search_path):
                            for item in os.listdir(search_path):
                                item_path = os.path.join(search_path, item)
                                if os.path.isdir(item_path):
                                    # Check common DCC app directory patterns
                                    if (app_name == "maya" and "Autodesk" in search_path and "Maya" in item) or \
                                       (app_name == "houdini" and "Side Effects Software" in search_path and "Houdini" in item) or \
                                       (app_name == "blender" and "Blender Foundation" in search_path) or \
                                       (app_name == "mari" and "Mari" in item) or \
                                       (app_name == "marmoset" and "Marmoset" in item):
                                        exe_path = os.path.join(item_path, exe_name)
                                        if os.path.exists(exe_path):
                                            found_apps.append({
                                                "name": app_name.replace("_", " ").title(),
                                                "path": exe_path
                                            })
                                            break
                    except (OSError, PermissionError):
                        continue
    
    # Remove duplicates based on path
    seen_paths = set()
    unique_apps = []
    for app in found_apps:
        if app["path"] not in seen_paths:
            seen_paths.add(app["path"])
            unique_apps.append(app)
    
    return unique_apps

def _add_app_if_valid(exe_path, found_apps):
    """Helper to determine app name and add to list."""
    app_name = None
    if "Blender" in exe_path:
        app_name = "blender"
    elif "Maya" in exe_path:
        app_name = "maya"
    elif "Houdini" in exe_path:
        app_name = "houdini"
    elif "Mari" in exe_path:
        app_name = "mari"
    elif "Toolbag" in exe_path:
        app_name = "marmoset"
    elif "Katana" in exe_path:
        app_name = "katana"
    elif "Gaea" in exe_path:
        app_name = "gaea"
    
    if app_name:
        found_apps.append({
            "name": app_name.replace("_", " ").title(),
            "path": exe_path
        })

@lru_cache(maxsize=None)
def get_search_paths() -> tuple[str]:
    """Returns a list of common installation directories."""
    paths = []
    if os.name == "nt":  # Windows
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        paths.extend([program_files, program_files_x86])
    else:  # macOS and Linux
        paths.extend(["/Applications", "/usr/local/bin", "/opt"])
    return tuple(paths)

def export_dcc_paths(session, dcc_apps, custom_path=None):
    """Exports the DCC application paths to a YAML file."""
    user_id = session.user_id if session.user_id else "default_user"
    
    if custom_path:
        if os.path.isdir(custom_path):
            output_path = os.path.join(custom_path, f"{user_id}_dcc.yaml")
        else:
            output_path = custom_path
        
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    else:
        # Default path using session's root_dir
        output_dir = os.path.join(session.root_dir, "Data", "roles", user_id)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{user_id}_dcc.yaml")

    yaml_data = []
    for app in dcc_apps:
        yaml_data.append({"name": app["name"], "path": app["path"]})
    
    with open(output_path, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
    
    console.print(f"[green]DCC paths exported to {output_path}[/green]")

def _dcc_help():
    """Displays detailed help for the 'dcc' command."""
    help_text = """
    [bold]NAME[/bold]
        dcc - Lists detected Digital Content Creation (DCC) applications.

    [bold]SYNOPSIS[/bold]
        [bold]dcc[/bold] [--export [PATH]]
        [bold]dcc[/bold] [|-h|--help|]

    [bold]DESCRIPTION[/bold]
        The `dcc` command scans common installation paths to find installed
        DCC applications. By default, it displays a table of found applications
        and their installation paths. The scan is performed only when necessary
        and the results are cached.

    [bold]OPTIONS[/bold]
        [bold]--export [PATH][/bold]
            Exports the detected DCC application paths to a YAML file.
            - If PATH is a directory, the file is saved as `<user_id>_dcc.yaml`.
            - If PATH is a file path, it is used directly.
            - If PATH is omitted, the default is `Data/roles/<user_id>/<user_id>_dcc.yaml`.

    [bold]EXAMPLES[/bold]
        - List all detected DCC applications:
          `dcc`

        - Export paths to the default location:
          `dcc --export`
          
        - Export paths to a custom directory:
          `dcc --export /path/to/custom/folder`
          
        - Export paths to a custom file:
          `dcc --export /path/to/custom/file.yaml`
    """
    console.print(Panel(help_text, title="DCC Command Help", expand=False, border_style="green"))

def dcc(session, args):
    """Lists all available DCC applications, with optimized scanning."""
    if "-h" in args or "--help" in args:
        _dcc_help()
        return

    # Argument validation
    if args and "--export" not in args:
        _dcc_help()
        return
    if "--export" in args and len(args) > 2:
        _dcc_help()
        return

    # Perform scan only when needed
    def ensure_scan():
        if not hasattr(session, 'dcc_apps') or not session.dcc_apps:
            with console.status("[bold green]Scanning for DCC applications...[/bold green]"):
                search_paths = get_search_paths()
                session.dcc_apps = scan_for_dcc_apps(search_paths)

    if "--export" in args:
        ensure_scan()
        export_index = args.index("--export")
        custom_path = args[export_index + 1] if export_index + 1 < len(args) else None
        export_dcc_paths(session, session.dcc_apps, custom_path)
        return

    if not args:
        ensure_scan()
        table = Table(title="DCC Applications")
        table.add_column("Application Name", style="cyan")
        table.add_column("Path", style="magenta")

        if not session.dcc_apps:
            console.print("[yellow]No DCC applications found.[/yellow]")
        else:
            for app in session.dcc_apps:
                table.add_row(app["name"], app["path"])
            console.print(table)
        return

def register_commands(registry):
    registry.register("dcc", dcc, aliases=["dcc_apps"])
