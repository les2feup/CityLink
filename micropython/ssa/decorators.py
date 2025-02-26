import time
import asyncio
from ssa.core import SSA
from typing import Callable, Awaitable

def ssa_task(period_ms: int = 0):
    """! Decorator to handle the publication of a property to the broker
        @param property: The property to publish
        @param period_ms: The period in milliseconds to publish the property (0 for one shot properties)
        @param retain: Whether the property should be retained by the broker
        @param qos: The MQTT quality of service level for the property

        The decorated function will be called in a loop, sleeping for the specified period
        after each call.
        The result of the decorated function will be published (on change) to the broker
        with the specified property name.
        If the property has an event associated with it, the event will be checked and published
        (if triggered) each cycle after the property is published.

        The decorated function should return the value to be published.
        The decorated function signature should be:
            async def func() -> Any

        Note: See ssa_main decorator documentation for example usage
    """
    def decorator(func: Awaitable[[SSA], None]):
        def wrapper():
            ssa_instance = SSA()
            while True:
                next_wake_time = ticks_add(time.ticks_ms(), period_ms)

                await func(ssa_instance)
                if period_ms == 0: # one shot task
                    break

                sleep_time = ticks_diff(next_wake_time, time.ticks_ms())
                if sleep_time > 0:
                    await asyncio.sleep_ms(sleep_time)

        return wrapper
    return decorator

def ssa_main(last_will: str = None):
    """! Decorator to create the main function of the application
        @param init_func: A function that takes an SSA instance as an argument
        and sets up the application property/event handlers and action callbacks.
        The function signature should be:
            def func(ssa: SSA) -> None

        The decorated function will be wrapped in an async function that will
        create an SSA instance, run the init function, connect to the broker
        and start the main loop.

        The code flow will be:
        1. Create an SSA instance
        2. Run the init function
        3. Connect to the broker
        4. Execute the SSA Network Registration process
        5. Start the main loop and service incoming messages and run the registered handlershandlers

        example usage:
    """
    def decorator(init_func: Callable[[SSA], None]):
        def main_wrapper():
            async def ssa_entry_point():
                ssa_instance = SSA()

                try:
                    init_func(ssa_instance)
                except Exception as e:
                    raise Exception(f"[ERROR] Failed to run initial setup: {e}")

                try:
                    ssa_instance.__connect(last_will)
                except Exception as e:
                    raise Exception(f"[ERROR] SSA connection failed: {e}") from e

                await ssa_instance.__main_loop()

            asyncio.run(ssa_entry_point())

        return main_wrapper
    return decorator
