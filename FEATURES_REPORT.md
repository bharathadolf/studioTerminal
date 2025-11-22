# Burra Paadu VFX Studio - Core Shell Features Report

## Overview
The Burra Paadu VFX Studio Core Shell is a specialized terminal environment designed for VFX studios to streamline workflows for artists, supervisors, and pipeline TDs. It provides a role-based command interface, automated DCC application discovery, and system diagnostics.

## Core Features

### 1. Role-Based Access Control (RBAC)
The shell implements a sophisticated role-based access control system with 5 distinct user roles:

- **Artist**: Basic navigation commands (`ls`, `cd`, `pwd`, `clear`, `help`)
- **Supe (Supervisor)**: All Artist commands plus `assign` and `showuser`
- **Pipe (Pipeline TD)**: All Supe commands plus `get_user`
- **Rnd (R&D Developer)**: All Pipe commands plus debugging tools
- **Master (Administrator)**: Full system access, including `userinfo` and role switching

### 2. Command System
The shell supports a comprehensive set of commands organized by role permissions:

#### Basic Commands (Available to all roles where permitted):
- `help`: Displays available commands based on user role
- `ll`: Displays current location where terminal is launched
- `ls`: Lists files in current directory
- `cd`: Changes directory
- `dir`: Displays subfolders in current directory
- `pwd`: Prints current working directory
- `clear`: Clears terminal screen while preserving banner
- `exit`: Exits the terminal
- `quit`: Terminates background processes

#### Advanced Commands (Role-restricted):
- `run`: Executes programs in background while keeping shell active
- `dcc`: Automatically scans and lists installed DCC applications
- `userinfo`: Generates detailed system and user reports (HTML/JSON/TXT)
- `assign`: Manages user roles and permissions
- `showuser`: Lists all users and their current roles

### 3. Background Process Management
- `run <program> [args...]`: Launches external programs in background
- `quit`: Terminates the last background process
- `quit --all`: Terminates all background processes
- Process tracking with PID management

### 4. DCC Application Discovery
- Automated scanning of common installation paths for VFX software
- Supports Maya, Houdini, Nuke, Blender, Substance Painter, Mari, Marmoset
- Caching mechanism to optimize scanning performance
- Export functionality to YAML format

### 5. System Information & Diagnostics
- Comprehensive system information collection using threading
- CPU, memory, disk, network, and GPU information
- Export to JSON, HTML, or TXT formats
- Persistent user ID generation and management
- Network statistics and battery information (where applicable)

### 6. User Management
- Persistent user ID generation stored in user's home directory
- Role assignment and management via `assign` command
- User listing with `showuser` command
- Configuration stored in JSON files

### 7. Rich User Interface
- Color-coded terminal output using the `rich` library
- Cinematic startup banner: "🎬 BURRA PAADU VFX STUDIO - CORE SHELL"
- Progress bars for system initialization and scanning
- Formatted tables for displaying information
- Command completion and syntax highlighting

### 8. Configuration Management
- Role-based command permissions stored in `Data/roles_config.json`
- User-to-role mapping in `Data/users_config.json`
- Validation of configuration files
- Fallback mechanisms for invalid configurations

### 9. Startup Automation
- Unified startup process that handles DCC scanning and user info generation
- Progress tracking with visual feedback
- Automatic generation of user info reports (HTML/JSON/TXT)
- DCC application scanning and YAML configuration generation
- Caching to prevent redundant operations

### 10. File Management
- Directory navigation with `cd`, `ls`, `dir`
- Working directory tracking
- Persistent user-specific file storage in `Data/roles/<user_id>/`

### 11. Process Management
- Background job submission and tracking
- Process termination with job management
- Support for running multiple background processes

### 12. Security Features
- Role-based command authorization
- Permission validation before command execution
- Master role can switch between all roles
- Non-master roles cannot switch roles

### 13. Export & Reporting
- System information export to multiple formats (JSON, HTML, TXT)
- DCC application paths export to YAML
- Persistent user reports generation
- Structured data output with rich formatting

### 14. Platform Support
- Windows-optimized (with Windows-specific paths and commands)
- Cross-platform compatibility considerations
- PATH environment variable integration

## Technical Architecture

### Core Components:
- **Shell Engine**: Main terminal loop with role management
- **Command Registry**: Centralized command registration and permission management
- **Session Management**: State tracking and user context
- **UI System**: Rich terminal interface with banners and formatting
- **System Utilities**: Configuration validation and file management

### File Structure:
```
Terminal/
├── Data/                    # Configuration and user data
│   ├── roles_config.json    # Role-based command permissions
│   └── users_config.json    # User-to-role mapping
├── Terminal/
│   ├── commands/           # Command implementations
│   ├── core/              # Core shell functionality
│   ├── ui/                # User interface components
│   └── utils/             # Utility functions
└── main.py                # Entry point
```

## Usage Characteristics
- Role-based command availability
- Persistent user sessions
- Automatic system initialization
- Rich visual feedback
- Background process support
- Configuration-driven permissions
- Cross-platform compatibility (optimized for Windows)

This terminal environment provides a comprehensive solution for VFX studio operations with security, automation, and user experience as key priorities.