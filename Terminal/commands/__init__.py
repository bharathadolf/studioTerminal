from . import assign
from . import basic
from . import show_users
from . import userInfo
from . import dcc # Import the dcc module

def register_all_commands(registry):
    basic.register_commands(registry)
    assign.register_commands(registry)
    show_users.register_commands(registry)
    userInfo.register_commands(registry)
    dcc.register_commands(registry)
