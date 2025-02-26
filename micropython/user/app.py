"""! Simple example app demonstrating the use of the Smart Sensor Actuator Hardware Abstraction Layer."""
import random
from ssa import * # Import the SSA class, @ssa_task and @ssa_main decorators

@ssa_task(2000)
async def random_event(ssa: SSA) -> None:
    """! Example event handler that triggers randomly.
    @returns Tuple[bool, str]: A tuple containing a boolean indicating whether the event occurred and a string message.
    """
    if random.randint(0, 1):
        ssa.trigger_event("random_event", "Event triggered")

@ssa_task(1000)
async def random_property_with_event(ssa: SSA) -> None:
    """! Example property handler that updates randomly.
    @returns int: A random integer value between 0 and 100.
    """
    new_value: int = random.randint(0, 100)
    ssa.set_property("random_value", new_value)
    if new_value > 70:
        ssa.trigger_event("random_value_event", "Random value is greater than 70")

def print_action(_ssa: SSA, msg: str) -> None:
    """! Example action that prints the received message payload."""
    print(f"Simple action triggered with message: {msg}")

@ssa_main(last_will = "Simple app exited unexpectedly")
def init(ssa: SSA):
    ssa.create_property("random_value", 0)

    ssa.create_task(random_event)
    ssa.create_task(random_property_with_event)

    ssa.create_action_callback("print_action", print_action)
