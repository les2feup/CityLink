"""! Simple app demonstrating the use of the Smart Sensor Actuator Hardware Abstraction Layer."""
import random
from ssa.core import SSA
from ssa.decorators import ssa_property_task, ssa_event_task, ssa_main
from typing import Tuple

def example_action_callback(msg: str):
    """! Example action callback that prints the received message payload."""
    print(f"Action triggered with message: {msg}")

@ssa_property_task("value", 2000)
async def example_prop_handler() -> int:
    """! Example property handler that updates randomly.
    @returns int: A random integer value between 0 and 100.
    """
    return random.randint(0, 100)

@ssa_event_task("example_event", 2000)
async def example_event_handler() -> Tuple[bool, str]:
    """! Example event handler that triggers randomly.
    @returns Tuple[bool, str]: A tuple containing a boolean indicating whether the event occurred and a string message.
    """
    return random.randint(0, 100) > 50, "Standalone event occurred"

@ssa_main
def init(ssa: SSA):
    ssa.set_property_event("value",
                           "example_prop_event",
                           lambda x: x > 50,
                           lambda x: f"Prop event! {x}")

    ssa.create_task(example_prop_handler)
    ssa.create_task(example_event_handler)

    ssa.action_callback("action", example_action_callback)
