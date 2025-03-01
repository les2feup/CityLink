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
    @param id: ID dictionary.
    @param config: Configuration dictionary.
    @param action_handler: The action handler for actions invoked by the
    WoT servient or other devices. Must support at least the core ssa actions.
    """
    def __init__(self, ssa_instance, id, config, action_handler):
        pass

    def launch(self, setup_func):
        """Launch the SSA runtime by connecting to the network 
        and sending registration messages.

        If the connection is successful, start running registered tasks
        and wait for incoming messages.

        @param setup_func: A setup function to run before starting the
        runtime. This is where the user code is initialized and 
        registered with the runtime.
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

    def create_task(self, task_func, task_name):
        """Create a task to be executed by the runtime.
        @param task_func: The function to execute.
        @param task_name: The name of the task.
        """
        pass
