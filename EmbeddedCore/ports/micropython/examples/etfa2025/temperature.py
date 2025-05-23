from citylink.core import EmbeddedCore
from micropython import const
from machine import Pin, ADC
from time import time, gmtime

# Constants
TEMP_GPIO = const(26)  # Pin number for the analog temperature sensor
TEMP_MIN = const(0)  # Minimum temperature value
TEMP_MAX = const(50)  # Maximum temperature value

ALARM_GPIO = const(16)  # Pin number for the alarm LED

OVERHEAT_TEMP = const(40)  # Overheat threshold in degrees Celsius

# HW setup
temp_sensor = ADC(Pin(TEMP_GPIO))
alarm = Pin(ALARM_GPIO, Pin.OUT)


@EmbeddedCore.sync_executor
def toggle_alarm_action(core: EmbeddedCore, state: bool):
    """Toggle the alarm LED on and off."""
    alarm.value(1 if state else 0)


@EmbeddedCore.sync_executor
def sample_temperature(core: EmbeddedCore) -> int:
    """Sample the temperature from the sensor."""
    raw_value = temp_sensor.read_u16()  # raw 0-65535 ADC reading

    # Convert the raw value to 0-100 degrees Celsius
    temperature = (raw_value / 65535) * 100
    if temperature < TEMP_MIN or temperature > TEMP_MAX:
        raise ValueError("Temperature out of range")

    if temperature > OVERHEAT_TEMP:
        core.emit_event(
            "overheating",
            {
                "timestamp": gmtime(time()),
                "alarm": alarm.value(),
                "temperature": temperature,
            },
        )

    core.set_property("temperature", temperature)

    return int(temperature)


def setup(core: EmbeddedCore):
    """Main function for the temperature sensor application.
    This function initializes the temperature sensor and starts the main loop.

    The runtime is initialized with the default configuration by the App() decorator
    and passed into the main function as the first argument.
    """
    core.create_property("temperature", 0.0)
    core.register_action_executor("toggleAlarm", toggle_alarm_action)
    core.task_create(
        "sample_temperature",
        sample_temperature,
        period_ms=1000,
    )
    pass
