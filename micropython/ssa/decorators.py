import time
import asyncio
from ssa.core import SSA
from typing import Callable, Awaitable

def ssa_task(period_ms: int = 0):
    """! Decorator to create a task function that will be executed
         @param period_ms: The period in milliseconds at which the task should be executed.

         note: The decorated function should be an async function that takes an SSA instance as an argument.
         The function signature should be:
            async def func(ssa: SSA) -> None
    """
    def decorator(func: Awaitable[[SSA], None]):
        async def ssa_task_wrapper():
            ssa_instance = SSA()
            while True:
                next_wake_time = time.ticks_add(time.ticks_ms(), period_ms)
                
                try:
                    await func(ssa_instance)
                except Exception as e:
                    raise Exception(f"[ERROR] Failed to run {func.__name__}: {e}") from e

                if period_ms == 0: # one shot task
                    break

                sleep_time = time.ticks_diff(next_wake_time, time.ticks_ms())
                if sleep_time > 0:
                    await asyncio.sleep_ms(sleep_time)

        return ssa_task_wrapper
    return decorator

def ssa_main(last_will: str = None):
    """! Decorator to create the main function of the application
        @param last_will: The last will message to be sent if the application exits unexpectedly.

        The decorated function will be wrapped in an async function that will
        create an SSA instance, run the init function, connect to the broker
        and start the main loop.

        The execution flow is as follows:
        1. Create an SSA instance
        2. Run the init function
        3. Connect to the broker
        4. Execute the SSA Network Registration process
        5. Start the main loop, service incoming messages and run tasks

        note: The decorated function should be a function that takes an SSA instance as an argument.
        The function signature should be:
            def init(ssa: SSA) -> None
    """
    def decorator(init_func: Callable[[SSA], None]):
        def main_wrapper():
            async def ssa_entry_point():
                ssa_instance = SSA()

                try:
                    init_func(ssa_instance)
                except Exception as e:
                    raise Exception(f"[ERROR] Failed to run initial setup: {e}") from e

                try:
                    ssa_instance.__connect(last_will)
                except Exception as e:
                    raise Exception(f"[ERROR] SSA connection failed: {e}") from e

                await ssa_instance.__main_loop()

            asyncio.run(ssa_entry_point())

        return main_wrapper
    return decorator
