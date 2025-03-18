from ._config import ConfigLoader
from .interfaces import SSARuntime


def ssa_main(runtime_class=None):
    """
    Decorator that wraps a main function to launch the SSA runtime.
    
    This decorator creates an SSA instance with the specified runtime_class and launches the
    runtime by invoking the decorated main function with the SSA instance as its argument.
    If no runtime_class is provided, it attempts to import a default runtime from the ssa_modules
    package and raises an exception if the import fails.
    
    Args:
        runtime_class: Optional runtime management class for the SSA instance.
    
    Raises:
        Exception: If no runtime_class is provided and the default runtime cannot be imported.
    """
    if not runtime_class:
        try:  # Default to ssa_modules default runtime if available
            from ssa_modules import DefaultRuntime

            runtime_class = DefaultRuntime
        except ImportError:
            raise Exception("No runtime class provided and no default available")

    def decorator(main):
        """
        Wraps a main function to launch the SSA runtime.
        
        Returns a function that, when invoked, creates an SSA instance using the specified runtime class and
        launches the runtime by calling the decorated main function with the SSA instance as its argument.
        """

        def main_wrapper():
            """
            Wraps the main function with SSA initialization and runtime launch.
            
            This function instantiates an SSA object using the provided runtime class and launches
            the SSA runtime, executing the user-defined main function with the SSA instance as an
            argument.
            """
            ssa = SSA(runtime_class)
            ssa.launch(lambda: main(ssa))

        return main_wrapper

    return decorator


class SSA:
    """
    The SSA class is the main class for the Smart Sensor Actuator framework
    """

    def __init__(self, runtime_class: SSARuntime):
        """
        Initializes an SSA instance with configuration and a runtime instance.
        
        Loads JSON configuration files from the './config' directory and creates a
        runtime instance using the provided runtime_class. Raises an exception if
        configuration loading or runtime instantiation fails.
        
        Args:
            runtime_class: A SSARuntime subclass used to instantiate the runtime with
                the loaded configuration.
        """

        def list_files():
            """
            Lists configuration file paths in the './config' directory.
            
            Scans the './config' directory for files and returns a list of strings representing each file's path.
            """
            import os

            config_files = [f"./config/{file}" for file in os.listdir("./config")]
            return config_files

        config_handler = ConfigLoader(list_files())

        try:
            config = config_handler.load_config()
        except Exception as e:
            raise Exception(f"[ERROR] Failed to load configuration: {e}") from e

        try:
            self._rt = runtime_class(config)
        except Exception as e:
            raise Exception(f"[ERROR] Failed to init runtime instance: {e}") from e

    def launch(self, user_main=None):
        """
        Launch the SSA runtime by connecting to the runtime instance and executing an optional callback.
        
        If a user-defined main function is provided as `user_main`, it is executed as part of the launch.
        If no callback is provided, the device is automatically registered before launching.
        Any exception raised during the launch is re-raised with additional context.
            
        Args:
            user_main: Optional callback function to run during the runtime launch.
            
        Raises:
            Exception: If the runtime fails to launch.
        """
        self._rt.connect()
        if not user_main:
            self._rt.register_device()

        try:
            self._rt.launch(user_main)
        except Exception as e:
            raise Exception(f"[ERROR] SSA runtime exited: {e}") from e

    def create_property(self, prop_name, prop_value, **kwargs):
        """
        Creates a property in the runtime.
        
        Delegates property creation to the runtime instance using the provided name and value.
        Additional keyword arguments are forwarded to the runtime's property creation method.
        """
        self._rt.create_property(prop_name, prop_value, **kwargs)

    def get_property(self, prop_name, **kwargs):
        """
        Retrieves the value of a property from the runtime.
        
        This method delegates the property lookup to the underlying runtime instance,
        forwarding the provided property name and any additional keyword arguments.
        
        Args:
            prop_name: The name or identifier of the property to retrieve.
            **kwargs: Additional arguments to pass to the runtime's property getter.
        
        Returns:
            The value associated with the specified property.
        """
        return self._rt.get_property(prop_name, **kwargs)

    async def set_property(self, name, value, **kwargs):
        """
        Asynchronously sets a property in the runtime.
        
        Delegates the update to the underlying runtime by calling its set_property method with
        the specified property name, value, and any additional keyword arguments. Returns the
        result of the runtime's property update operation.
        """
        return await self._rt.set_property(name, value, **kwargs)

    async def emit_event(self, name, value, **kwargs):
        """
        Asynchronously emits an event to the runtime.
        
        Sends an event with the specified name and value to the runtime instance.
        Any additional keyword arguments are passed to the underlying runtime method.
        
        Args:
            name: The identifier for the event.
            value: The event data to be emitted.
            **kwargs: Additional parameters forwarded to the runtime.
        
        Returns:
            The result of the runtime's event emission.
        """
        return await self._rt.emit_event(name, value, **kwargs)

    def register_action(self, action_uri, action_callback):
        """
        Registers an action handler with the runtime.
        
        Wraps the provided callback so that the SSA instance is automatically passed as
        the first argument when the action is invoked, and registers the resulting handler
        with the runtime using the specified action URI.
        
        Args:
            action_uri: Identifier for the action to be handled.
            action_callback: Callable that processes the action input; it should accept the SSA
                             instance as its first argument.
        """
        def ssa_model_action(action_input, **kwargs):
            return action_callback(self, action_input, **kwargs)

        self._rt.register_action_handler(action_uri, ssa_model_action)

    def rt_task_create(self, task_id, task_func, task_period_ms):
        """
        Registers a periodic task for execution via the runtime scheduler.
        
        Creates an asynchronous loop that repeatedly calls the provided task function with
        the SSA instance as its argument. The task is invoked at intervals defined by the
        given period in milliseconds; if the period is 0, the task is executed only once.
        Any exceptions raised during the task execution are propagated with additional 
        context.
            
        Parameters:
            task_id: A unique identifier for the scheduled task.
            task_func: An asynchronous callback function to execute.
            task_period_ms: Interval in milliseconds between successive task invocations;
                            a value of 0 indicates a one-shot task.
        """

        import time

        async def ssa_task():
            """Run a periodic or one-shot asynchronous task.
            
            This helper function continually executes a provided asynchronous task function,
            ensuring each run aligns with a scheduled period in milliseconds. It calculates the
            next wake time and waits for the remaining time before the next iteration. A period
            of zero results in a single execution. Any exception raised during the task execution
            is propagated with additional context.
            """
            while True:
                next_wake_time = time.ticks_add(time.ticks_ms(), task_period_ms)

                try:
                    await task_func(self)
                except Exception as e:
                    raise Exception(
                        f"[ERROR] Failed to run {task_func.__name__}: {e}"
                    ) from e

                if task_period_ms == 0:  # one shot task
                    break

                sleep_time = time.ticks_diff(next_wake_time, time.ticks_ms())
                if sleep_time > 0:
                    await self._rt.task_sleep_ms(sleep_time)

        self._rt.task_create(task_id, ssa_task)

    def rt_task_cancel(self, task_id):
        """
        Cancel a scheduled task.
        
        Requests the runtime to cancel the task identified by the given task_id, which should
        have been registered via rt_task_create.
        
        Args:
            task_id: Unique identifier of the task to cancel.
        """
        self._rt.task_cancel(task_id)

    async def rt_task_sleep_s(self, s):
        """
        Asynchronously pause execution for a specified number of seconds.
        
        Delegates to the runtime's sleep function to wait asynchronously for the
        given duration.
        
        Args:
            s: The duration to sleep, in seconds.
        """
        await self._rt.task_sleep_s(s)

    async def rt_task_sleep_ms(self, ms):
        """Asynchronously sleep for the specified number of milliseconds.
        
        Args:
            ms (int): The duration to pause execution, in milliseconds.
        """
        await self._rt.task_sleep_ms(ms)
