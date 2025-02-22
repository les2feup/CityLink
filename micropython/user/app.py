import time
import random

from ssa.core import SSA
from ssa.decorators import ssa_property_handler, ssa_event_handler, ssa_main

def example_action_callback(msg: str):
    print(f"Action triggered with message: {msg}")

@ssa_property_handler("value", 2000)
async def example_prop_handler():
    return random.randint(0, 100)

@ssa_event_handler("event", 2000)
async def example_event_handler():
    return random.randint(0, 100) > 50, "Event occurred"

@ssa_main
def init(ssa: SSA):
    ssa.register_handler(example_prop_handler)
    ssa.register_handler(example_event_handler)
    ssa.action_callback("action", example_action_callback)

if __name__ == "__main__":
    print("[WARNING] user/app.py should not be run directly. Please run ssa/bootstrap.py instead.")
