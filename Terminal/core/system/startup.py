import os
from typing import List, Callable

class StartupCommandManager:
    def __init__(self):
        self.startup_commands: List[Callable] = []

    def register(self, command: Callable):
        """
        Decorator to register a function to be run at terminal startup.
        """
        self.startup_commands.append(command)
        return command

startup_manager = StartupCommandManager()
