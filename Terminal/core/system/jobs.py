import threading
import time
from rich.console import Console

console = Console()

class JobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()
        self.next_job_id = 1

    def submit_job(self, command_func, args, session, command_name):
        """
        Submits a command to run in the background.
        """
        job_id = self.next_job_id
        self.next_job_id += 1

        def job_wrapper():
            try:
                # Notify start
                if session.current_role in ['rnd', 'pipe']:
                    console.print(f"\n[dim][Background Job {job_id} ({command_name}) started][/dim]")
                
                # Execute
                command_func(session, args)
                
                # Notify completion
                with self.lock:
                    if job_id in self.jobs:
                        del self.jobs[job_id]
                
                if session.current_role in ['rnd', 'pipe']:
                    console.print(f"\n[bold green][Background Job {job_id} ({command_name}) completed][/bold green]")
                    # Re-print prompt hint if needed, but tricky in async
            except Exception as e:
                console.print(f"\n[bold red][Background Job {job_id} failed: {e}][/bold red]")

        thread = threading.Thread(target=job_wrapper, daemon=True)
        with self.lock:
            self.jobs[job_id] = {
                'thread': thread,
                'command': command_name,
                'start_time': time.time()
            }
        
        thread.start()
        console.print(f"[green][{job_id}] {command_name} running in background[/green]")
        return job_id

    def list_jobs(self):
        """Lists currently running jobs."""
        with self.lock:
            if not self.jobs:
                console.print("No background jobs running.")
                return

            console.print("[bold]Running Jobs:[/bold]")
            for job_id, info in self.jobs.items():
                duration = round(time.time() - info['start_time'], 1)
                console.print(f"[{job_id}] {info['command']} (running for {duration}s)")

job_manager = JobManager()
