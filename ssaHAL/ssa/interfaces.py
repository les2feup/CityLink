class SSAConnector:
    """Base class defining the SSAConnector interface."""
    def __init__(self, config):
        """Initialize the SSAConnector base class."""
        raise NotImplementedError("Subclasses must implement __init__")

    async def connect(self):
        """Attempt to the Edge Node's SSA IoT Connector"""
        raise NotImplementedError("Subclasses must implement connect()")

    async def disconnect(self):
        """Disconnect from the network."""
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    async def register_device(self):
        """Register the device with the WoT servient."""
        raise NotImplementedError("Subclasses must implement register_device()")

class AffordanceHandler:
    """Base class defining the AffordanceHandler interface."""
    def __init__(self, config):
        """Initialize the AffordanceHandler base class."""

    def create_property(self, prop_name, prop_value, **kwargs):
        """Create a new property."""
        raise NotImplementedError("Subclasses must implement create_property()")

    def get_property(self, prop_name, **kwargs):
        """Get the value of a property."""
        raise NotImplementedError("Subclasses must implement get_property()")

    async def set_property(self, prop_name, prop_value, **kwargs):
        """Set the value of a property."""
        raise NotImplementedError("Subclasses must implement set_property()")

    async def emit_event(self, event_name, event_data, **kwargs):
        """Publish an event to all subscribers."""
        raise NotImplementedError("Subclasses must implement emit_event()")

    def register_action_handler(self, action_name, action_func, **kwargs):
        """Register a new action."""
        raise NotImplementedError("Subclasses must implement register_action()")

class SSARuntime(SSAConnector, AffordanceHandler):
    """Base class defining the SSARuntime interface."""
    def __init__(self, config, extra_config_template={}):
        """Initialize SSARuntime with a required configuration dictionary."""
        self.tasks = {}  # This ensures all implementors will have a tasks attribute
        self.properties = {}  # This ensures all implementors will have a properties attribute
        self.config = config

        default_config_template = {
                "tm": {
                    "name": str,
                    "version": {
                        "model": str,
                        "instance": str
                        }
                    }
                }

        extra_config_template.update(default_config_template)

        def validate_configuration(template, provided, path="config"):
            if not isinstance(provided, dict):
                raise ValueError(f"{path} must be a dictionary")

            for key, expected_type in template.items():
                if key not in provided:
                    raise ValueError(f"Missing required key: {path}['{key}']")

                if isinstance(expected_type, dict):
                    validate_configuration(expected_type,
                                           provided[key],
                                           f"{path}['{key}']")

                elif not isinstance(provided[key], expected_type):
                    raise TypeError(
                    f"Expected {path}['{key}'] to be {expected_type.__name__}, "
                    f"but got {type(provided[key]).__name__}"
                )

        validate_configuration(extra_config_template, config)

    def launch(self, extra_init_func=None):
        """Launch the runtime."""
        raise NotImplementedError("Subclasses must implement launch()")

    def rt_task_create(self, task_id, task_func):
        """Register a task for execution."""
        raise NotImplementedError("Subclasses must implement rt_task_create()")

    def rt_task_cancel(self, task_id):
        """Cancel a previously registered task."""
        raise NotImplementedError("Subclasses must implement rt_task_cancel()")

    async def rt_task_sleep_s(self, s):
        """Sleep for a given number of seconds."""
        raise NotImplementedError("Subclasses must implement rt_task_sleep_s()")

    async def rt_task_sleep_ms(self, ms):
        """Sleep for a given number of milliseconds."""
        raise NotImplementedError("Subclasses must implement rt_task_sleep_ms()")

