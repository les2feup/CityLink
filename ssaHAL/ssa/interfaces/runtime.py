from .connector import SSAConnector
from .affordance_handler import AffordanceHandler


class SSARuntime(SSAConnector, AffordanceHandler):
    """Base class defining the SSARuntime interface."""
    def __init__(self, config):
        """Initialize SSARuntime with a required configuration dictionary."""
        self.config = config

        default_config_template = {
            "tm": {"name": str, "version": {"model": str, "instance": str}}
        }

        extra_config_template.update(default_config_template)

        def validate_configuration(template, provided, path="config"):
            if not isinstance(provided, dict):
                raise ValueError(f"{path} must be a dictionary")

            for key, expected_type in template.items():
                if key not in provided:
                    raise ValueError(f"Missing required key: {path}['{key}']")

                if isinstance(expected_type, dict):
                    validate_configuration(
                        expected_type, provided[key], f"{path}['{key}']"
                    )

                elif not isinstance(provided[key], expected_type):
                    raise TypeError(
                        f"Expected {path}['{key}'] to be {expected_type.__name__}, "
                        f"but got {type(provided[key]).__name__}"
                    )

        validate_configuration(extra_config_template, config)

    def connect(self):
        """Attempt to the Edge Node's SSA IoT Connector"""
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self):
        """Disconnect from the network."""
        raise NotImplementedError("Subclasses must implement disconnect()")

    def start_scheduler(self, setup_func=None):
        """Launch the runtime."""
        raise NotImplementedError("Subclasses must implement launch()")

    def task_create(self, task_id, task_func):
        """Register a task for execution."""
        raise NotImplementedError("Subclasses must implement rt_task_create()")

    def task_cancel(self, task_id):
        """Cancel a previously registered task."""
        raise NotImplementedError("Subclasses must implement rt_task_cancel()")

    async def task_sleep_s(self, s):
        """Sleep for a given number of seconds."""
        raise NotImplementedError("Subclasses must implement rt_task_sleep_s()")

    async def task_sleep_ms(self, ms):
        """Sleep for a given number of milliseconds."""
        raise NotImplementedError("Subclasses must implement rt_task_sleep_ms()")
