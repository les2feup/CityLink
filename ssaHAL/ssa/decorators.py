import time
import asyncio

from .core import SSA
from ssa_modules import uMQTTRuntime, GenericWLANDriver

def ssa_task(period_ms: int = 0):
    """
    Wraps an asynchronous function into a periodic task.
    
    This decorator converts an async function that takes an SSA instance into a task that runs
    either once (if period_ms is 0) or repeatedly every period_ms milliseconds. The decorated
    function should follow the signature:
        async def func(ssa: SSA) -> None.
    
    Args:
        period_ms (int): The interval between consecutive executions in milliseconds. A value of 0
                         indicates a single execution.
    """
    def decorator(func):
        """
        Wraps an async function to run as a periodic SSA task.
        
        The returned wrapper repeatedly executes the decorated function with an SSA 
        instance provided as its argument. Execution intervals are determined 
        externally by a 'period_ms' variable. When 'period_ms' is 0, the function 
        runs only once; otherwise, it runs repeatedly, waiting for the next scheduled 
        time based on system ticks. Any exception raised during execution is caught 
        and re-raised with additional error context.
        
        Note:
            'period_ms' must be defined in the enclosing scope to specify the interval 
            in milliseconds.
        
        Raises:
            Exception: If the decorated function fails during execution.
        """
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

def ssa_main(nic_class = GenericWLANDriver,
             runtime_class = uMQTTRuntime):
    """Wraps the main function with an SSA instance launcher.
             
             This decorator instantiates an SSA object using the provided network interface
             controller (nic_class) and runtime (runtime_class) classes, then launches the
             application via the decorated main function.
             
             Args:
                 nic_class: Network interface controller class to use (default: GenericWLANDriver).
                 runtime_class: Asynchronous runtime management class (default: AsyncioMQTTRuntime).
             """
    def decorator(main):
        """
        Wraps the main function to launch the SSA runtime.
        
        Returns a new function that creates an SSA instance using the configured network interface and runtime classes,
        and then launches the application by invoking the provided main function.
        """
        def main_wrapper():
            ssa_instance = SSA(nic_class, runtime_class)
            ssa_instance.launch(main)
        return main_wrapper
    return decorator
