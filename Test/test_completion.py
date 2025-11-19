"""
Test/test_completion.py

This script demonstrates how the autocompletion dictionary is structured and how it maps
to the actual completion logic. This serves as a verification and documentation of the flow.
"""

import sys
import os

# Add project root to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Terminal.ui.completer import create_completer
from prompt_toolkit.document import Document

def test_autocompletion_flow():
    print("=== Autocompletion Flow Verification ===\n")
    
    # 1. Initialize the completer
    completer = create_completer()
    print("[1] Completer Initialized")
    print(f"    Type: {type(completer).__name__}")
    
    # 2. Inspect the internal dictionary structure
    # NestedCompleter stores options in .options dict
    print("\n[2] Dictionary Mapping (Top Level Commands):")
    for command in completer.options.keys():
        print(f"    - {command}")
        
    # 3. Verify Nested Completions (e.g., userinfo)
    print("\n[3] Verifying Nested Context (e.g., 'userinfo'):")
    userinfo_completer = completer.options.get('userinfo')
    if userinfo_completer:
        print("    'userinfo' has the following sub-options:")
        for flag in userinfo_completer.options.keys():
            print(f"      -> {flag}")
            
            # Check deeper nesting (e.g., --export arguments)
            flag_completer = userinfo_completer.options.get(flag)
            if flag_completer and flag_completer.options:
                print(f"         Arguments for {flag}: {list(flag_completer.options.keys())}")
    
    # 4. Simulate User Input
    print("\n[4] Simulating User Input:")
    
    # Case A: Typing 'dcc ' -> Should suggest flags
    text = "dcc "
    doc = Document(text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))
    print(f"    Input: '{text}'")
    print(f"    Suggestions: {[c.text for c in completions]}")
    
    # Case B: Typing 'userinfo --export ' -> Should suggest formats
    text = "userinfo --export "
    doc = Document(text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))
    print(f"    Input: '{text}'")
    print(f"    Suggestions: {[c.text for c in completions]}")

    # Case C: Typing 'assign --role ' -> Should suggest roles
    text = "assign --role "
    doc = Document(text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))
    print(f"    Input: '{text}'")
    print(f"    Suggestions: {[c.text for c in completions]}")

    # Case D: Typing 'assign ' -> Should suggest user IDs and flags
    text = "assign "
    doc = Document(text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))
    print(f"    Input: '{text}'")
    # Filter for a known ID to verify dynamic loading without printing everything
    known_id = "4d8d28d3232b" 
    has_id = any(c.text == known_id for c in completions)
    print(f"    Contains user ID '{known_id}': {has_id}")
    
    # Case E: Typing 'assign <user_id> ' -> Should suggest user actions
    text = f"assign {known_id} "
    doc = Document(text, cursor_position=len(text))
    completions = list(completer.get_completions(doc, None))
    print(f"    Input: '{text}'")
    print(f"    Suggestions: {[c.text for c in completions]}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    test_autocompletion_flow()
