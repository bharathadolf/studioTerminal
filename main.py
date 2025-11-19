import os
from Terminal.core.shell import TerminalShell
import Terminal.core.system.startup_processes

if __name__ == "__main__":
    ROOT_DIR = os.getcwd()
    shell = TerminalShell(ROOT_DIR)
    shell.run()
