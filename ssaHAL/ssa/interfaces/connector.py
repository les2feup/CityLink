class SSAConnector:
    """Base class defining the SSAConnector interface."""

    def __init__(self, config):
        """Initialize the SSAConnector base class."""
        raise NotImplementedError("Subclasses must implement __init__")

    def connect(self):
        """Attempt to the Edge Node's SSA IoT Connector"""
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self):
        """Disconnect from the network."""
        raise NotImplementedError("Subclasses must implement disconnect()")

    def register_device(self):
        """Register the device with the WoT servient."""
        raise NotImplementedError("Subclasses must implement register_device()")
