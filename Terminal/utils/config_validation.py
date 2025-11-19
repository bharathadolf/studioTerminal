
from typing import Dict, List, Any, Optional

def validate_roles_config(data: Any) -> tuple[bool, Optional[str]]:
    """
    Validates the roles configuration structure.
    Expected: Dict[role_name: str, commands: List[str]]
    """
    if not isinstance(data, dict):
        return False, "Root must be a dictionary."

    for role, role_data in data.items():
        if not isinstance(role, str):
            return False, f"Role key '{role}' must be a string."
        
        if not isinstance(role_data, dict):
            return False, f"Data for role '{role}' must be a dictionary."
            
        commands = role_data.get("allowed_commands")
        if commands is None:
             # It's possible a role has no commands or uses a different structure, but based on the file, it should have this.
             # Let's be strict for now or allow it if we want to support other keys.
             # Given the error, we expect allowed_commands.
             return False, f"Role '{role}' is missing 'allowed_commands' list."

        if not isinstance(commands, list):
            return False, f"allowed_commands for role '{role}' must be a list."
            
        for cmd in commands:
            if not isinstance(cmd, str):
                return False, f"Command '{cmd}' in role '{role}' must be a string."

    return True, None

def validate_users_config(data: Any, valid_roles: List[str] = None) -> tuple[bool, Optional[str]]:
    """
    Validates the users configuration structure.
    Expected: Dict[user_id: str, role: str]
    """
    if not isinstance(data, dict):
        return False, "Root must be a dictionary."

    for user_id, role in data.items():
        if not isinstance(user_id, str):
            return False, f"User ID '{user_id}' must be a string."
        if not isinstance(role, str):
            return False, f"Role '{role}' for user '{user_id}' must be a string."
        
        if valid_roles and role not in valid_roles:
            return False, f"Role '{role}' for user '{user_id}' is not a valid role (allowed: {valid_roles})."

    return True, None
