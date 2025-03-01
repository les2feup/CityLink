import time
import asyncio

from ssa_modules import AsyncioMQTTRuntime, GenericWLANDriver

def ssa_task(period_ms: int = 0):
    """Decorator to create a task function that will be executed
    @param period_ms: The period in milliseconds at which the task
    should be executed.

    note: The decorated function should be an async function that
    takes an SSA instance as an argument.
    The function signature should be:
        async def func(ssa: SSA) -> None
    """
    def decorator(func):
        async def ssa_task_wrapper(ssa_instance):
            while True:
                next_wake_time = time.ticks_add(time.ticks_ms(), period_ms)

                try:
                    await func(ssa_instance)
                except Exception as e:
                    raise Exception(f"[ERROR] Failed to run\
                            {func.__name__}: {e}") from e

                if period_ms == 0: # one shot task
                    break

                sleep_time = time.ticks_diff(next_wake_time, time.ticks_ms())
                if sleep_time > 0:
                    await asyncio.sleep_ms(sleep_time)

        return ssa_task_wrapper
    return decorator

def ssa_main(network_driver_class = GenericWLANDriver,
             runtime_class = AsyncioMQTTRuntime):
    """! Decorator to create the main function of the application
    @param network_driver_class: The network driver class to use.
    @param runtime_class: The runtime class to use.
    """
    def decorator(main):
        def main_wrapper():
            ssa_instance = SSA(network_driver_class, runtime_class)
            ssa_instance.launch(main)

        return main_wrapper
    return decorator
