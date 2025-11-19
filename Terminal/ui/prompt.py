from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from rich.console import Console

console = Console()

def make_session(history_file, command_list):
    return PromptSession(
        history=FileHistory(history_file),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(command_list, ignore_case=True),
    )

def fallback_input(prompt_text):
    try:
        return input(prompt_text)
    except (KeyboardInterrupt, EOFError):
        return None
