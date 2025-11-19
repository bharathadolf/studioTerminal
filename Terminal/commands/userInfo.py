import os
import getpass
import platform
import socket
import uuid
import hashlib
import psutil
import subprocess
import re
import sys
import json
import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..utils.command_utils import validate_args

try:
    import GPUtil
except ImportError:
    GPUtil = None

try:
    import requests
except ImportError:
    requests = None

VALID_ARGS = ["-h", "--help", "--uid", "--export", "--output", "--log"]

# ------------------------------
# Persistent User ID
# ------------------------------
def get_persistent_user_id(app_name: str = "sysinfo") -> str:
    """Generate or load a persistent user ID stored in the user's home directory."""
    home = Path.home()
    uid_dir = home / f".{app_name}"
    uid_file = uid_dir / "user_id.txt"

    if uid_file.exists():
        with open(uid_file, "r") as f:
            uid = f.read().strip()
            if uid:
                return uid

    # First run: generate and save
    uid_dir.mkdir(exist_ok=True)
    import time
    seed = f"{getpass.getuser()}{time.time()}{os.getpid()}".encode()
    uid = hashlib.sha256(seed).hexdigest()[:12]  # 12-char hex

    with open(uid_file, "w") as f:
        f.write(uid)

    return uid


# ------------------------------
# Configuration
# ------------------------------
@dataclass
class Config:
    """Configuration for system info gathering"""
    include_network: bool = True
    include_disk: bool = True
    include_battery: bool = True
    include_processes: bool = True
    include_public_ip: bool = False  # Requires internet
    top_processes_count: int = 5
    export_format: Optional[str] = None  # 'json', 'html', 'txt'
    output_path: Optional[str] = None
    log_mode: str = "on"


# ------------------------------
# Data Models
# ------------------------------
@dataclass
class SystemInfo:
    username: str
    hostname: str
    os_type: str
    os_version: str
    platform: str
    architecture: str
    cpu: str
    cpu_cores: int
    cpu_threads: int
    cpu_freq_mhz: float
    cpu_usage_percent: float
    ram_total_gb: float
    ram_available_gb: float
    ram_usage_percent: float
    swap_total_gb: float
    swap_usage_percent: float
    gpu_info: Optional[str]
    local_ip: str
    mac_address: str
    public_ip: Optional[str]
    python_version: str
    virtualenv: str
    current_directory: str
    boot_time: str
    uptime: str
    timezone: str
    unique_id: str


# ------------------------------
# Cached & Optimized Functions
# ------------------------------

def get_public_ip(timeout: int = 5) -> Optional[str]:
    """Get public IP address"""
    if not requests:
        return None

    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=timeout)
        return response.json()['ip']
    except Exception:
        return None


def get_cpu_info() -> Dict[str, Any]:
    """Detailed CPU information"""
    cpu_freq = psutil.cpu_freq()
    return {
        "processor": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_frequency_mhz": cpu_freq.max if cpu_freq else 0,
        "current_frequency_mhz": cpu_freq.current if cpu_freq else 0,
        "usage_percent": psutil.cpu_percent(interval=1)
    }


def get_memory_info() -> Dict[str, Any]:
    """Detailed memory information"""
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": round(vm.total / 1e9, 2),
        "available_gb": round(vm.available / 1e9, 2),
        "used_gb": round(vm.used / 1e9, 2),
        "usage_percent": vm.percent,
        "swap_total_gb": round(swap.total / 1e9, 2),
        "swap_used_gb": round(swap.used / 1e9, 2),
        "swap_percent": swap.percent
    }


def get_disk_info() -> List[Dict[str, Any]]:
    """Disk/partition information"""
    disks = []
    for partition in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "total_gb": round(usage.total / 1e9, 2),
                "used_gb": round(usage.used / 1e9, 2),
                "free_gb": round(usage.free / 1e9, 2),
                "usage_percent": usage.percent
            })
        except PermissionError:
            continue
    return disks


def get_battery_info() -> Optional[Dict[str, Any]]:
    """Battery information (laptops)"""
    battery = psutil.sensors_battery()
    if not battery:
        return None

    return {
        "percent": battery.percent,
        "plugged_in": battery.power_plugged,
        "time_left_minutes": battery.secsleft // 60 if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
    }


def get_top_processes(count: int = 5) -> List[Dict[str, Any]]:
    """Get top processes by CPU and memory"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Sort by CPU usage
    processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
    return processes[:count]


@lru_cache(maxsize=1)
def get_default_gateway() -> Optional[str]:
    """Get default gateway (cached), silencing stderr."""
    system_type = platform.system().lower()
    try:
        if system_type == "windows":
            result = subprocess.check_output(
                "ipconfig", shell=True, text=True, encoding="utf-8", 
                errors="ignore", timeout=3, stderr=subprocess.DEVNULL
            )
            match = re.search(r"Default Gateway.*?:\s*([\d\.]+)", result)
            return match.group(1) if match else None
        else:
            result = subprocess.check_output(
                "ip route show default", shell=True, text=True, 
                timeout=3, stderr=subprocess.DEVNULL
            )
            match = re.search(r"default via ([\d\.]+)", result)
            return match.group(1) if match else None
    except Exception:
        return None


def get_network_info() -> List[Dict[str, Any]]:
    """Enhanced network information"""
    network_data = []
    system_type = platform.system().lower()

    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        io_counters = psutil.net_io_counters(pernic=True)

        for interface, snic_list in addrs.items():
            info = {
                "name": interface,
                "status": "Up" if stats.get(interface) and stats[interface].isup else "Down",
                "ip_address": None,
                "mac_address": None,
                "speed_mbps": stats[interface].speed if stats.get(interface) else 0,
                "gateway": None,
                "connection__type": "Unknown",
                "bytes_sent_mb": 0,
                "bytes_recv_mb": 0
            }

            # IP and MAC
            for snic in snic_list:
                if snic.family == socket.AF_INET:
                    info["ip_address"] = snic.address
                elif snic.family == psutil.AF_LINK:
                    info["mac_address"] = snic.address

            # Connection type
            name_lower = interface.lower()
            if any(x in name_lower for x in ["wi-fi", "wlan", "wireless"]):
                info["connection_type"] = "Wi-Fi"
            elif any(x in name_lower for x in ["eth", "lan", "ethernet"]):
                info["connection_type"] = "Ethernet"
            elif "lo" in name_lower:
                info["connection_type"] = "Loopback"

            # Traffic stats
            if interface in io_counters:
                io = io_counters[interface]
                info["bytes_sent_mb"] = round(io.bytes_sent / 1e6, 2)
                info["bytes_recv_mb"] = round(io.bytes_recv / 1e6, 2)

            # Gateway
            if info["ip_address"]:
                info["gateway"] = get_default_gateway()

            network_data.append(info)
    except Exception:
        # Silently fail on network info errors
        pass

    return network_data


def get_gpu_info() -> Optional[str]:
    """GPU information"""
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                return ', '.join([f"{gpu.name} ({gpu.memoryTotal}MB)" for gpu in gpus])
        except:
            pass
    return None


def get_timezone() -> str:
    """Get system timezone, silencing stderr."""
    try:
        if platform.system().lower() == "windows":
            result = subprocess.check_output(
                "tzutil /g", shell=True, text=True, timeout=2, stderr=subprocess.DEVNULL
            )
            return result.strip()
        else:
            try:
                result = subprocess.check_output(
                    "timedatectl show -p Timezone --value", 
                    shell=True, text=True, timeout=2, stderr=subprocess.DEVNULL
                )
                return result.strip()
            except (FileNotFoundError, subprocess.CalledProcessError):
                if os.path.exists("/etc/timezone"):
                    with open("/etc/timezone", "r") as f:
                        return f.read().strip()
                return "Unknown"
    except Exception:
        return "Unknown"

# ... (The rest of the file remains the same)

# ------------------------------
# Main Collector with Threading
# ------------------------------
class SystemInfoCollector:
    """Collect system information with parallel processing"""

    def __init__(self, config: Config = Config()):
        self.config = config
        self.console = Console()

    def collect_all(self) -> Dict[str, Any]:
        """Collect all system information using threading"""
        data = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._collect_basic_info): 'basic',
                executor.submit(self._collect_cpu_info): 'cpu',
                executor.submit(self._collect_memory_info): 'memory',
            }

            if self.config.include_disk:
                futures[executor.submit(get_disk_info)] = 'disks'

            if self.config.include_network:
                futures[executor.submit(get_network_info)] = 'network'

            if self.config.include_battery:
                futures[executor.submit(get_battery_info)] = 'battery'

            if self.config.include_processes:
                futures[executor.submit(get_top_processes, self.config.top_processes_count)] = 'top_processes'

            if self.config.include_public_ip:
                futures[executor.submit(get_public_ip, 5)] = 'public_ip' # 5 seconds timeout

            for future in as_completed(futures):
                key = futures[future]
                try:
                    data[key] = future.result()
                except Exception as e:
                    data[key] = f"Error: {str(e)}"

        # Merge basic info into root
        if 'basic' in data:
            basic = data.pop('basic')
            data.update(basic)

        return data

    def _collect_basic_info(self) -> Dict[str, Any]:
        """Collect basic system information"""
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time

        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except:
            local_ip = "127.0.0.1"

        mac = ':'.join(re.findall('..', f"{uuid.getnode():012x}"))

        return {
            "username": getpass.getuser(),
            "hostname": platform.node(),
            "os_type": platform.system(),
            "os_version": platform.version(),
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "local_ip": local_ip,
            "mac_address": mac,
            "python_version": platform.python_version(),
            "virtualenv": os.environ.get('VIRTUAL_ENV', 'None'),
            "current_directory": os.getcwd(),
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": str(uptime).split('.')[0],
            "timezone": get_timezone(),
            "unique_id": get_persistent_user_id("sysinfo"),
            "gpu_info": get_gpu_info()
        }

    def _collect_cpu_info(self) -> Dict[str, Any]:
        return get_cpu_info()

    def _collect_memory_info(self) -> Dict[str, Any]:
        return get_memory_info()

    def print_info(self):
        """Print collected information"""
        data = self.collect_all()

        if self.config.log_mode == "on":
            self._print_rich(data)

        # Export if configured
        if self.config.export_format and self.config.output_path:
            self.export(data, self.config.output_path)

    def _print_rich(self, data: Dict[str, Any]):
        """Print using rich library"""
        console = self.console

        # System Info Table
        table = Table(title="💻 System Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Value", style="green")

        # Basic info
        basic_fields = ['username', 'hostname', 'os_type', 'os_version', 'platform',
                        'architecture', 'local_ip', 'mac_address', 'python_version',
                        'boot_time', 'uptime', 'timezone', 'unique_id']

        for field in basic_fields:
            if field in data:
                table.add_row(field.replace('_', ' ').title(), str(data[field]))

        if 'public_ip' in data and data['public_ip']:
            table.add_row("Public IP", str(data['public_ip']))

        console.print(table)

        # CPU Table
        if 'cpu' in data and isinstance(data['cpu'], dict):
            cpu_table = Table(title="🖥️  CPU Information", show_header=True)
            cpu_table.add_column("Property", style="cyan")
            cpu_table.add_column("Value", style="yellow")

            for key, value in data['cpu'].items():
                cpu_table.add_row(key.replace('_', ' ').title(), str(value))

            console.print(cpu_table)

        # Memory Table
        if 'memory' in data and isinstance(data['memory'], dict):
            mem_table = Table(title="💾 Memory Information", show_header=True)
            mem_table.add_column("Property", style="cyan")
            mem_table.add_column("Value", style="yellow")

            for key, value in data['memory'].items():
                mem_table.add_row(key.replace('_', ' ').title(), str(value))

            console.print(mem_table)

        # Disk Table
        if 'disks' in data and isinstance(data['disks'], list):
            disk_table = Table(title="💿 Disk Information", show_header=True)
            disk_table.add_column("Device", style="cyan")
            disk_table.add_column("Mount", style="blue")
            disk_table.add_column("Total (GB)", justify="right")
            disk_table.add_column("Used (GB)", justify="right")
            disk_table.add_column("Free (GB)", justify="right")
            disk_table.add_column("Usage %", justify="right", style="red")

            for disk in data['disks']:
                disk_table.add_row(
                    disk['device'],
                    disk['mountpoint'],
                    str(disk['total_gb']),
                    str(disk['used_gb']),
                    str(disk['free_gb']),
                    f"{disk['usage_percent']}%"
                )

            console.print(disk_table)

    def export(self, data: Dict[str, Any], filename: str):
        """Export data to file"""
        if self.config.export_format == 'json':
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        elif self.config.export_format == 'html':
            html = self._generate_html(data)
            with open(filename, 'w') as f:
                f.write(html)
        
        elif self.config.export_format == 'txt':
            with open(filename, 'w') as f:
                for section, content in data.items():
                    if isinstance(content, dict):
                        f.write(f"--- {section.replace('_', ' ').title()} ---\n")
                        for key, value in content.items():
                            f.write(f"{key}: {value}\n")
                    elif isinstance(content, list):
                        f.write(f"--- {section.replace('_', ' ').title()} ---\n")
                        if content and isinstance(content[0], dict):
                            for item in content:
                                for key, value in item.items():
                                    f.write(f"{key}: {value}\n")
                                f.write("\n")
                    else:
                        f.write(f"{section}: {content}\n")
                    f.write("\n")

    def _generate_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML report"""
        # CSS styles are now in a separate string to avoid format issues.
        styles = """
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #333; }
            h2 { color: #555; border-bottom: 2px solid #ccc; padding-bottom: 5px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; background: white; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
        """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>System Information Report</title>
            <style>{styles}</style>
        </head>
        <body>
            <h1>System Information Report</h1>
            <p>Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        """

        # Add tables for each section
        for section, content in data.items():
            # Skip sections that are not dicts or lists (like 'public_ip')
            if not isinstance(content, (dict, list)):
                 html += f"<h2>{section.replace('_', ' ').title()}</h2><p>{content}</p>"
                 continue

            if isinstance(content, dict):
                html += f"<h2>{section.replace('_', ' ').title()}</h2><table>"
                html += "<tr><th>Property</th><th>Value</th></tr>"
                for key, value in content.items():
                    html += f"<tr><td>{key}</td><td>{value}</td></tr>"
                html += "</table>"
            elif isinstance(content, list) and content:
                 if isinstance(content[0], dict):
                    html += f"<h2>{section.replace('_', ' ').title()}</h2><table>"
                    # Table headers
                    html += "<tr>" + "".join([f"<th>{k.replace('_', ' ').title()}</th>" for k in content[0].keys()]) + "</tr>"
                    # Table rows
                    for item in content:
                        html += "<tr>" + "".join([f"<td>{v}</td>" for v in item.values()]) + "</tr>"
                    html += "</table>"

        html += "</body></html>"
        return html


def show_help():
    """Displays help information for the userInfo command."""
    console = Console()
    table = Table(title="userInfo Command Help", show_header=True, header_style="bold cyan")
    table.add_column("Argument", style="dim", width=20)
    table.add_column("Description")
    table.add_column("Example")

    table.add_row("-h, --help", "Show this help message.", "userInfo --help")
    table.add_row("--uid", "Display the unique user ID.", "userInfo --uid")
    table.add_row("--export [format]", "Export system info to a file (json, html, txt).", "userInfo --export json")
    table.add_row("--output [path]", "Specify the output path for the export.", "userInfo --export json --output /path/to/file.json")

    console.print(table)


def user_info_command(session, args: List[str]):
    """Main function to handle userInfo command."""
    console = Console()

    if "-h" in args or "--help" in args:
        show_help()
        return

    if validate_args(args, VALID_ARGS, show_help):
        return

    if "--uid" in args:
        console.print(get_persistent_user_id("sysinfo"))
        return

    config = Config()

    if "--export" in args:
        try:
            format_index = args.index("--export") + 1
            config.export_format = args[format_index]
        except (IndexError, ValueError):
            console = Console()
            console.print("[red]Error: --export requires a format (json, html, txt).[/red]")
            return

    if "--output" in args:
        try:
            path_index = args.index("--output") + 1
            config.output_path = args[path_index]
        except (IndexError, ValueError):
            console = Console()
            console.print("[red]Error: --output requires a file path.[/red]")
            return
            
    if "--log" in args:
        try:
            log_index = args.index("--log") + 1
            config.log_mode = args[log_index]
        except (IndexError, ValueError):
            pass

    collector = SystemInfoCollector(config)
    collector.print_info()

def register_commands(registry):
    registry.register("userinfo", user_info_command)
