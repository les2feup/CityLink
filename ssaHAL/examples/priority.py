"""
This is a simple SSA application that simulates a sensor that generates random values.
The sensor value is then sent to different topics based on the priority of the sensor.
The priority of the sensor is set by the user and can be "low", "medium", or "high".
Setting the priority is handled by the user through the SSA HAL API (topic is mqtt://{...}/actions/ssa_hal/set/priority)
"""
import random
from ssa import SSA, ssa_task, ssa_main

@ssa_task(1000) # Poll sensor every 1 second
async def simulate_random_sensor(ssa: SSA) -> None:
    sensor_value = random.randint(0, 100)
    priority = ssa.get_property("priority")
    ssa.trigger_event(f"sensor_value/{priority}_prio", sensor_value) #"low_prio", "medium_prio", "high_prio"

@ssa_main()
def main(ssa: SSA):
    ssa.create_property("priority", "low") # "low", "medium", "high"
    ssa.create_task(simulate_random_sensor)
