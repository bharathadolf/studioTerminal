import os
import json
from prompt_toolkit.completion import NestedCompleter

def _get_user_ids():
    """Reads user IDs from Data/users_config.json."""
    config_path = os.path.join("Data", "users_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                return set(data.keys())
        except (json.JSONDecodeError, IOError):
            pass
    return set()

def _get_assign_completion_dict():
    """Generates the dynamic completion dictionary for the 'assign' command."""
    
    # Common roles
    roles = {'artist', 'supe', 'pipe', 'rnd', 'master'}
    
    # Arguments allowed after selecting a user ID
    user_actions = {
        '--role': roles,
        '--category': roles,
        '--add-command': None, 
        '--remove-command': None
    }
    
    # Arguments allowed after selecting --role <role_name>
    role_actions = {
        '--add-command': None,
        '--remove-command': None
    }
    
    # Build the dictionary
    assign_dict = {
        '-h': None,
        '--help': None,
        '--role': {role: role_actions for role in roles}, # assign --role <role> ...
    }
    
    # Add user IDs dynamically
    user_ids = _get_user_ids()
    for user_id in user_ids:
        assign_dict[user_id] = user_actions # assign <user_id> ...
        
    return assign_dict

def create_completer():
    """
    Creates and returns a NestedCompleter for the terminal session.
    """
    completion_dict = {
        'help': None,
        'll': None,
        'ls': None,
        'cd': None,
        'dir': None,
        'pwd': None,
        'clear': None,
        'run': None,
        'exit': None,
        
        # Commands with flags/arguments
        'dcc': {
            '--export': None,
            '--help': None,
            '-h': None,
        },
        'quit': {
            '--all': None,
            '--help': None,
            '-h': None,
        },
        'userinfo': {
            '--export': {'html', 'json', 'txt'},
            '--output': None,
            '--log': {'on', 'off'},
            '--help': None,
        },
        'showuser': None,
        'assign': _get_assign_completion_dict(), # Dynamic generation
    }
    
    return NestedCompleter.from_nested_dict(completion_dict)
