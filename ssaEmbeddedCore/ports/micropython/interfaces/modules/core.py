from .modules.affordance_handler import AffordanceHandler
from .modules.taskScheduler import TaskScheduler
from .modules.serializer import Serializer

class SSACore(AffordanceHandler, TaskScheduler):
    """Base class defining the SSARuntime interface."""

    def __init__(self, config_dir, default_serializer: Serializer):
        """Initialize SSARuntime with a required configuration dictionary."""
        self.config_dir = config_dir
        self.serializer = default_serializer

    def _load_config(self):
        """Load the configuration from the specified directory."""
        raise NotImplementedError("Subclasses must implement load_config()")

    def _connect(self):
        """Attempt to the Edge Node's SSA IoT Connector"""
        raise NotImplementedError("Subclasses must implement connect()")

    def _disconnect(self):
        """Disconnect from the network."""
        raise NotImplementedError("Subclasses must implement disconnect()")

    def _listen(self):
        """Listen and handle incoming requests."""
        raise NotImplementedError("Subclasses must implement listen()")

    def _register_device(self):
        """
        Registers the device with the WoT servient.

        Send registration request to the WoT servient to register the device.
        Wait for registration confirmation before proceeding.

        Subclasses must override this method to implement the device registration logic.
        """
        raise NotImplementedError("Subclasses must implement register_device()")

    def SSACoreEntry(*args, **kwargs):
        """Decorator to mark the entry point for the SSACore."""

        def main_decorator(main_func):
            """Decorates the main function of the SSACore."""

            def main_wrapper(self):
                """Wrapper for the main function of the SSACore."""
                raise NotImplementedError("Subclasses must implement SSACoreEntry()")

            return main_wrapper

        return main_decorator
