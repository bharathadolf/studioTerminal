
import os
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console

from .startup import startup_manager
from Terminal.commands.dcc import get_search_paths, scan_for_dcc_apps
from Terminal.commands.userInfo import get_persistent_user_id, user_info_command

console = Console()

@startup_manager.register
def unified_startup_process(session):
    """
    A unified startup process to handle both DCC scanning and user info generation sequentially.
    This prevents race conditions and provides a single, clean progress bar.
    """
    user_id = get_persistent_user_id("sysinfo")
    dcc_output_dir = os.path.join(session.root_dir, "Data", "roles", user_id)
    dcc_output_path = os.path.join(dcc_output_dir, f"{user_id}_dcc.yaml")
    
    user_info_log_dir = os.path.join(session.root_dir, "Data", "roles", user_id)
    user_info_formats = ["html", "json", "txt"]

    # --- Pre-checks to determine what needs to be run ---
    dcc_scan_needed = not os.path.exists(dcc_output_path)
    
    def is_file_valid(filepath):
        return os.path.exists(filepath) and os.path.getsize(filepath) > 0

    # Ensure user info dir exists before checking files
    os.makedirs(user_info_log_dir, exist_ok=True)
    missing_user_info_files = [f for f in user_info_formats if not is_file_valid(os.path.join(user_info_log_dir, f"{user_id}.{f}"))]
    user_info_needed = bool(missing_user_info_files)

    # --- Calculate total steps for the progress bar ---
    total_steps = 0
    if dcc_scan_needed:
        total_steps += 2 # 2 steps for DCC: scan, write
    if user_info_needed:
        total_steps += len(missing_user_info_files)
        
    if total_steps == 0:
        console.log("DCC & User Info: All configurations and reports are up to date. Skipping.")
        return

    # --- Run the combined process with a single progress bar ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]System Initialization", total=total_steps)

        # --- User Info Generation Logic ---
        if user_info_needed:
            for format_type in missing_user_info_files:
                output_path = os.path.join(user_info_log_dir, f"{user_id}.{format_type}")
                progress.update(task, description=f"Generating user {format_type} report...")
                
                args = ["--export", format_type, "--output", output_path, "--log", "off"]
                user_info_command(session, args)
                progress.advance(task)
            
            console.log(f"User Info auto-gen: Generated/updated {len(missing_user_info_files)} report(s).")
        else:
             console.log("User Info auto-gen: All report files already exist and are valid. Skipping.")
        
        # --- DCC Scan Logic ---
        if dcc_scan_needed:
            progress.update(task, description="Scanning for DCC applications...")
            dcc_apps = scan_for_dcc_apps(get_search_paths())
            if not hasattr(session, 'dcc_apps') or not session.dcc_apps:
                session.dcc_apps = dcc_apps
            progress.advance(task)

            progress.update(task, description="Writing DCC configuration...")
            yaml_data = []
            if dcc_apps:
                yaml_data = [{"name": app["name"], "path": app["path"]} for app in dcc_apps]
            
            with open(dcc_output_path, "w") as f:
                yaml.dump(yaml_data, f, default_flow_style=False)
            
            console.log(f"DCC auto-scan: Generated config for {len(dcc_apps)} app(s).")
            progress.advance(task)
        else:
            console.log("DCC auto-scan: Configuration file already exists. Skipping.")
            


    console.log("[green]System initialization complete.[/green]")
