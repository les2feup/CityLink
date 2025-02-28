class NetworkDriver():
    """
    Interface for network drivers.
    @param config: Configuration dictionary.
    """
    def __init__(self, config):
        pass

    def connect(self, retries, base_timeout, **kwargs):
        """Connect to the network.
        @param retries: Number of retries to attempt.
        @param base_timeout: Base timeout (in seconds)
        increases exponentially with each retry.
        @raise Exception: If connection fails.
        """
        pass

    def disconnect(self):
        """Disconnect from the network."""
        pass

    def get_ip(self):
        """Get the IP address of the device.
        @return The IP address as a string or None if not connected.
        """
        pass

class SSARuntime():
    """Interface for the SSA runtime.
    The SSA runtime is responsible for managing task scheduling and 
    for handling communication with the WoT servient.

    A copy of the SSA instance is passed to the runtime, allowing it to
    pass it to the user code.

    @param ssa_instance: The SSA instance.
    @param config: Configuration dictionary.
    """
    def __init__(self, ssa_instance, id, config):
        pass

    def launch(self, user_entry=None):
        """Launch the SSA runtime by connecting to the network 
        and sending registration messages.

        If the connection is successful, start running registered tasks
        and wait for incoming messages.

        @param user_entry: The entry point for the user code. If not provided,
        the runtime will wait for incoming messages.
        """
        pass

    def sync_property(self, property_name, value, **kwargs):
        """Synchronize a property with the WoT servient.
        @param property_name: The name of the property.
        @param value: The value of the property.
        """
        pass

    def trigger_event(self, event_name, payload, **kwargs):
        """Trigger an event, sending it to the WoT servient.
        @param event_name: The name of the event.
        @param payload: The payload of the event.
        @param special_args: Special arguments for the event.
        Like with properties, these are runtime dependend and are 
        ignored if not understood.

        @return True if the event was triggered successfully, False otherwise.
        """
        pass

    def register_action_handler(self, handler_func):
        """Register callback to execute when an action is invoked
        by the WoT servient

        @param handler_func: The callback function to execute
        must accept two arguments: action URI and message payload
        
        def handler_func(uri, payload):
            pass
        """
        pass

    def create_task(self, task_func, task_name):
        """Create a task to be executed by the runtime.
        @param task_func: The function to execute.
        @param task_name: The name of the task.
        """
        pass
