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
