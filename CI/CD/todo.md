# Termina Development To-Do List

## 🚨 Critical Fixes

- [x] **Command Parsing**: Fix space handling in arguments using `shlex`. (Current Task)
- [x] **Relative Paths**: Fix dependency on `os.getcwd()` by using `__file__` relative paths.

## 🏗️ Architecture

- [x] **Command Registry**: Decouple `shell.py` from specific commands using a registry pattern.
- [x] **Async Execution**: Move heavy commands off the main thread to prevent UI freezing. (Implemented via `&` and `JobManager`)

## 🛡️ Robustness

- [x] **Config Validation**: Add schema validation/error handling for JSON configs.
- [ ] **Logging**: Implement proper logging to file instead of just printing errors.

## 🧹 Refactoring

- [ ] **Assign Command**: Split `assign.py` into UI, Logic, and Data layers.

## ✨ New Features

- [ ] **Project Contexts**: `show <name>` command.
- [ ] **Environment Vars**: `setenv`/`getenv` per role.
- [ ] **Aliases**: `alias` command.
- [ ] **Plugins**: Drop-in `.py` file support.
- [ ] **Log Viewer**: TUI log viewer.
