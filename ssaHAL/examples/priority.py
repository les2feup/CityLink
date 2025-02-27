"""
@brief Simple app that demonstrates how to trigger events based on a property that is updated from an action.
In this example, a sensor value is generated randomly and an event is triggered based on the priority level of the sensor value.
A broker can subscribe to the events and take actions based on the priority level.
The priority level can be updated using an action, based on external decisions from the network.
"""
import random
from ssa import SSA, ssa_task, ssa_main

@ssa_task(1000) # Poll sensor every 1 second
async def simulate_random_sensor(ssa: SSA) -> None:
    sensor_value = random.randint(0, 100)
    priority = ssa.get_property("priority")
    ssa.trigger_event(f"sensor_value/{priority}_prio", sensor_value) #"low_prio", "medium_prio", "high_prio"

@ssa_main(last_will = "Simple app exited unexpectedly")
def init(ssa: SSA):
    ssa.create_property("priority", "low") # "low", "medium", "high"
    ssa.create_task(simulate_random_sensor)
