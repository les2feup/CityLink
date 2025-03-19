class AffordanceHandler:
    """Base class defining the AffordanceHandler interface."""

    def __init__(self, config):
        """Initialize the AffordanceHandler base class."""
        raise NotImplementedError("Subclasses must implement __init__()")

    def create_property(self, prop_name, prop_value, **kwargs):
        """Create a new property."""
        raise NotImplementedError("Subclasses must implement create_property()")

    def get_property(self, prop_name, **kwargs):
        """Get the value of a property."""
        raise NotImplementedError("Subclasses must implement get_property()")

    def set_property(self, prop_name, prop_value, **kwargs):
        """Set the value of a property."""
        raise NotImplementedError("Subclasses must implement set_property()")

    def set_action_callback(self, action_name, action_cb, **kwargs):
        """Register a new action."""
        raise NotImplementedError("Subclasses must implement register_action()")

    def get_action_callback(self, action_name, **kwargs):
        """Get the callback function for an action."""
        raise NotImplementedError("Subclasses must implement get_action_callback()")
