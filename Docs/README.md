# 🎬 Burra Paadu VFX Studio - Core Shell

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

Welcome to the **Burra Paadu VFX Studio Core Shell**, a specialized terminal environment designed to streamline workflows for artists, supervisors, and pipeline TDs. This shell provides a role-based command interface, automated DCC (Digital Content Creation) application discovery, and system diagnostics.

---

## 🚀 Features

### 🎭 Role-Based Access Control (RBAC)

The shell adapts its capabilities based on the user's assigned role. Security and workflow integrity are maintained by restricting commands to specific roles.

| Role       | Description   | Key Permissions                                             |
| :--------- | :------------ | :---------------------------------------------------------- |
| **Artist** | Standard user | Basic navigation (`ls`, `cd`, `pwd`), `clear`, `help`       |
| **Supe**   | Supervisor    | All Artist commands + `assign`, `showuser`                  |
| **Pipe**   | Pipeline TD   | All Supe commands + `get_user`                              |
| **Rnd**    | R&D Developer | All Pipe commands + Debugging tools                         |
| **Master** | Administrator | Full system access, including `userinfo` and role switching |

### 🛠️ Core Commands

- **`run <program>`**: Launch external programs in the background while keeping the shell active.
- **`dcc`**: Automatically scans and lists installed DCC applications (Maya, Nuke, Blender, etc.).
- **`userinfo`**: Generates detailed system and user reports (HTML/JSON/TXT).
- **`assign`**: Manage user roles and permissions (Supervisors+).
- **`showuser`**: List all users and their current roles.

### ⚡ Automated Startup

On launch, the system performs a "Unified Startup Process":

1.  **DCC Scanning**: Auto-detects installed VFX software and generates a configuration YAML.
2.  **User Profiling**: Generates persistent user info reports to `Data/roles/<user_id>/`.

---

## 📂 Project Structure

```text
Termina/
├── Data/
│   ├── roles/
│   ├── roles_config.json
│   └── users_config.json
├── Docs/
│   └── README.md
├── Terminal/
│   ├── commands/
│   │   ├── basic.py
│   │   ├── dcc.py
│   │   └── userInfo.py
│   ├── core/
│   │   ├── session.py
│   │   ├── shell.py
│   │   └── startup_processes.py
│   ├── ui/
│   │   └── banner.py
│   └── utils/
└── main.py
```

## 💻 Usage

### Starting the Shell

Run the `main.py` entry point:

```bash
python main.py
```

### Basic Navigation

```bash
[artist][studio]$ ls        # List files
[artist][studio]$ cd Data   # Change directory
[artist][studio]$ clear     # Clear screen (preserves banner!)
```

### Running Background Tasks

```bash
[master][studio]$ run notepad.exe
Started process 1234: notepad.exe
```

### Managing Processes

```bash
[master][studio]$ quit      # Kill last process
[master][studio]$ quit --all # Kill all background processes
```

---

## 🎨 Visuals

The terminal features a rich UI powered by the `rich` library, including:

- **Startup Banner**: A cinematic "BURRA PAADU VFX STUDIO" header.
- **Colored Output**: Command results, errors, and tables are color-coded for readability.
- **Progress Bars**: Visual feedback during system initialization and scanning.

---

## 🔧 Configuration

- **`Data/roles_config.json`**: Define command permissions per role.
- **`Data/users_config.json`**: Map user IDs to roles.

---

_Built with ❤️ for the VFX Community._
