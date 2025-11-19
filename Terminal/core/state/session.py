from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from Terminal.ui.completer import create_completer

class Session:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.current_role = 'artist' # Default role
        self.prompt_session = PromptSession(completer=create_completer())
        self.user_id = None
        self.roles_config = {}
        self.users_config = {}
        self.processes = []
        self.dcc_apps = [] # Initialize dcc_apps as an empty list

    def get_prompt(self):
        return FormattedText([
            ('ansiblue', f'[{self.current_role}]'),
            ('ansigreen', '[studio]'),
            ('ansimagenta', '$ '),
        ])

    def set_role(self, role):
        self.current_role = role

    def prompt(self, prompt_text):
        return self.prompt_session.prompt(prompt_text)