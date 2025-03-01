"""! Simple example app demonstrating the use of the Smart Sensor Actuator Hardware Abstraction Layer."""
import random
from ssa import SSA, ssa_task, ssa_main

@ssa_task(2000)
async def random_event(ssa: SSA) -> None:
    """! Example event handler that triggers randomly."""
    if random.randint(0, 1):
        ssa.trigger_event("random_event", "Event triggered")

@ssa_task(1000)
async def random_property_with_event(ssa: SSA) -> None:
    """! Example task that sets a random value to a property and triggers an event if the value is greater than 70."""
    new_value: int = random.randint(0, 100)
    ssa.set_property("random_value", new_value)
    if new_value > 70:
        ssa.trigger_event("random_value_event", "Random value is greater than 70")

def print_action(_ssa: SSA, msg: str) -> None:
    """! Example action that prints the received message payload."""
    print(f"Simple action triggered with message: {msg}")

@ssa_main()
def main(ssa: SSA):
    ssa.create_task(random_event)
    ssa.create_task(random_property_with_event)

    ssa.register_action("print_action", print_action)
