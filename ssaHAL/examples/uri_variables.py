"""
This is an example of how to use URI variables in the action callback.
"""
import random
from ssa import SSA, ssa_task, ssa_main

def print_action(_ssa: SSA, msg: str) -> None:
    print(f"Simple action triggered with message: {msg}")

def print_hello(_ssa: SSA, msg: str, name1: str, name2: str) -> None:
    print(f"Hello {name1}! {name2} sent you this message: {msg}")

def print_hello_world(_ssa: SSA, msg: str, name1: str) -> None:
    print(f"Hello World! {name1} is sent this message: {msg}")

@ssa_main(last_will = "Simple app exited unexpectedly")
def main(ssa: SSA):
    """
    Registers URI-based action callbacks with the provided SSA instance.
    
    This function maps three URI patterns to their corresponding callback functions:
    - "print_action" is registered with the simple action callback.
    - "print_hello/{name1}/{name2}" is registered with the greeting action that incorporates two names.
    - "print_hello/{name1}/world" is registered with the greeting action that includes "Hello World!".
    """
    ssa.register_action("print_action", print_action)
    ssa.register_action("print_hello/{name1}/{name2}", print_hello)
    ssa.register_action("print_hello/{name1}/world", print_hello_world)
