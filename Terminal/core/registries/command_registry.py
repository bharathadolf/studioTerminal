
class CommandRegistry:
    def __init__(self):
        self.commands = {}
        self.aliases = {}
        self.allowed_commands = set()

    def register(self, name, command, aliases=None):
        self.commands[name] = command
        if aliases:
            for alias in aliases:
                self.aliases[alias] = name

    def get_command(self, name):
        """Gets a command by its name or alias, checking if it's allowed."""
        command_name = self.aliases.get(name, name)
        if command_name in self.allowed_commands:
            return self.commands.get(command_name)
        return None

    def set_allowed_commands(self, allowed_commands):
        """Sets the list of allowed commands for the current role."""
        self.allowed_commands = set(allowed_commands)

    def get_all_commands(self):
        """Returns all registered commands, regardless of the current role."""
        return self.commands
