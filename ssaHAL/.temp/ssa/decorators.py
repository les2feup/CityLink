import time
import asyncio
from .core import SSA
from ssa_modules import AsyncioMQTTRuntime, GenericWLANDriver


def ssa_task(period_ms: int=0):

    def decorator(func):

        async def ssa_task_wrapper(ssa_instance):
            while True:
                next_wake_time = time.ticks_add(time.ticks_ms(), period_ms)
                try:
                    await func(ssa_instance)
                except Exception as e:
                    raise Exception(
                        f'[ERROR] Failed to run                            {func.__name__}: {e}'
                        ) from e
                if period_ms == 0:
                    break
                sleep_time = time.ticks_diff(next_wake_time, time.ticks_ms())
                if sleep_time > 0:
                    await asyncio.sleep_ms(sleep_time)
        return ssa_task_wrapper
    return decorator


def ssa_main(nic_class=GenericWLANDriver, runtime_class=AsyncioMQTTRuntime):

    def decorator(main):

        def main_wrapper():
            ssa_instance = SSA(nic_class, runtime_class)
            ssa_instance.launch(main)
        return main_wrapper
    return decorator
