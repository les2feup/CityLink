class SSAConnector:
    """Base class defining the SSAConnector interface."""

    def __init__(self, config):
        """Initialize the SSAConnector base class."""
        raise NotImplementedError("Subclasses must implement __init__")

    def _send_registration_message(self):
        """Register the device with the WoT servient."""
        raise NotImplementedError("Subclasses must implement register_device()")

    def execute_registration_procedure(self):
        """Register a new thing with the WoT servient."""
        raise NotImplementedError("Subclasses must implement register_thing()")

    def core_action_executor(self, action_name):
        """Handle the execution of the built-in ssa core actions."""
        raise NotImplementedError("Subclasses must implement core_action_executor()")

    def update_core_status(self, status, status_message):
        """Update the core status property"""
        raise NotImplementedError("Subclasses must implement update_core_status()")

    def get_core_status(self):
        """Get the current core status property"""
        raise NotImplementedError("Subclasses must implement get_core_status()")

