"""
This is a simple SSA application that simulates a sensor that generates random values.
The sensor value is then sent to different topics based on the priority of the sensor.
The priority of the sensor is set by the user and can be "low", "medium", or "high".
Setting the priority is handled by the user through the SSA HAL API (topic is mqtt://{...}/actions/ssa_hal/set/priority)
"""

import random
from ssa.core import ssa_main, SSA

async def simulate_random_sensor(ssa: SSA) -> None:
    """
    Simulate a sensor reading and trigger a corresponding event.

    This asynchronous function generates a random integer between 0 and 100 to represent a sensor value.
    It retrieves the current priority level from the SSA properties and triggers an event on the topic
    formatted as 'sensor_value/<priority>_prio', where <priority> may be 'low', 'medium', or 'high'.
    """
    sensor_value = random.randint(0, 100)
    priority = ssa.get_property("priority")
    await ssa.emit_event (
        f"sensor_value/{priority}_prio", sensor_value
    )  # "low_prio", "medium_prio", "high_prio"


@ssa_main()
def main(ssa: SSA):
    """
    Initializes the sensor simulation application.

    Creates a default "priority" property set to "low" and registers the sensor
    simulation task to generate sensor values. Valid priority values include
    "low", "medium", and "high".
    """
    ssa.create_property("priority", "low")  # "low", "medium", "high"
    ssa.rt_task_create("sensor_sim", simulate_random_sensor, 1000)  # 1 Hz
