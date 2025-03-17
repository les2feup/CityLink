from ._config import ConfigLoader
from .interfaces import SSARuntime


def ssa_main(runtime_class=None):
    """Wraps the main function with an SSA instance launcher.

    This decorator instantiates an SSA object using the provided network interface
    controller (nic_class) and runtime (runtime_class) classes, then launches the
    application via the decorated main function.

    Args:
        nic_class: Network interface controller class to use (default: GenericWLANDriver).
        runtime_class: Asynchronous runtime management class (default: AsyncioMQTTRuntime).
    """
    if not runtime_class:
        try:  # Default to ssa_modules default runtime if available
            from ssa_modules import Runtime

            runtime_class = Runtime
        except ImportError:
            raise Exception("No runtime class provided and no default available")

    def decorator(main):
        """
        Wraps the main function to launch the SSA runtime.

        Returns a new function that creates an SSA instance using the configured network interface and runtime classes,
        and then launches the application by invoking the provided main function.
        """

        def main_wrapper():
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
        Initializes a new SSA instance.

        Loads configuration from predefined JSON files and sets up the network
        interface and runtime components using the provided driver classes.
        Also initializes the global action handler and the internal property
        storage.

        Raises:
            Exception: Configuration loading or component initialization fails.

        Args:
            nic_class: The NetworkDriver implementation to use
            runtime_class: The SSARuntime implementation to use
        """

        def list_files():
            import os

            config_files = [f"./config/{file}" for file in os.listdir("./config")]
            return config_files

        config_handler = ConfigLoader(list_files())

        try:
            # Configuration Module
            config = config_handler.load_config()
            self._rt: SSARuntime = runtime_class(config)
        except Exception as e:
            raise Exception(f"[ERROR] Failed to init SSA instance: {e}") from e

    def launch(self, user_main=None):
        """
        Launch the SSA runtime and execute optional user code.

        This method registers actions for firmware and property updates, then
        launches the runtime environment using an optional user-defined
        callback. If the runtime fails to launch, the raised exception i
        propagated with additional context. Upon successful termination,
        an informational message is printed.

        Raises:
            Exception: If the network connection fails.
            Exception: If the runtime fails to launch.

        Args:
            user_main: Optional callback function to execute as part of the
            runtime.
        """
        self._rt.connect()
        if not user_main:
            self._rt.register_device()

        try:
            self._rt.launch(user_main)
        except Exception as e:
            raise Exception(f"[ERROR] SSA runtime exited: {e}") from e

    def create_property(self, prop_name, prop_value, **kwargs):
        self._rt.create_property(prop_name, prop_value, **kwargs)

    def get_property(self, prop_name, **kwargs):
        return self._rt.get_property(prop_name, **kwargs)

    async def set_property(self, name, value, **kwargs):
        return await self._rt.set_property(name, value, **kwargs)

    async def emit_event(self, name, value, **kwargs):
        return await self._rt.emit_event(name, value, **kwargs)

    def register_action(self, action_uri, action_callback):
        def action_wrapper(action_input, **kwargs):
            action_callback(self, action_input, **kwargs)

        self._rt.register_action(action_uri, action_wrapper)

    def rt_task_create(self, task_id, task_func, task_period_ms):
        """Register a task for execution."""

        import time

        async def ssa_task():
            while True:
                next_wake_time = time.ticks_add(time.ticks_ms(), task_period_ms)

                try:
                    await task_func(self)
                except Exception as e:
                    raise Exception(
                        f"[ERROR] Failed to run {func.__name__}: {e}"
                    ) from e

                if task_period_ms == 0:  # one shot task
                    break

                sleep_time = time.ticks_diff(next_wake_time, time.ticks_ms())
                if sleep_time > 0:
                    await self.rt_task_sleep_ms(sleep_time)

        self._rt.task_create(task_id, ssa_task)

    def rt_task_cancel(self, task_id):
        """Cancel a previously registered task."""
        self._rt.task_cancel(task_id)

    async def rt_task_sleep_s(self, s):
        """Sleep for a given number of seconds."""
        self._rt.task_sleep_s(s)

    async def rt_task_sleep_ms(self, ms):
        """Sleep for a given number of milliseconds."""
        self._rt.task_sleep_ms(ms)
