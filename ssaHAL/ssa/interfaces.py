class NetworkDriver():
    """
    Interface for network drivers.
    @param config: Configuration dictionary.
    """
    def __init__(self, config):
        """
        Initializes the NetworkDriver with the provided configuration.
        
        Args:
            config: A dictionary of network configuration options.
        """
        raise NotImplementedError

    def connect(self, retries, base_timeout_ms, **kwargs):
        """
        Attempts to establish a network connection with exponential backoff.
        
        This method attempts to connect to the network by performing the specified number
        of retries. The timeout between retries starts at the given base timeout (in seconds)
        and increases exponentially with each subsequent attempt. Additional keyword
        arguments can be used to customize the connection behavior.
        
        Args:
            retries: The number of connection attempts.
            base_timeout: The initial timeout in seconds, which scales exponentially with each retry.
            **kwargs: Additional parameters to modify the connection process.
        
        Raises:
            Exception: If the connection fails after all retry attempts.
        """
        raise NotImplementedError

    def disconnect(self):
        """Disconnect from the network."""
        raise NotImplementedError

    def get_ip(self):
        """
        Retrieves the device's IP address.
        
        Returns:
            str or None: The device's IP address if connected, or None otherwise.
        """
        raise NotImplementedError

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
        """Initialize an SSARuntime instance.
        
        Sets up the runtime interface for managing task scheduling and communication with the
        WoT servient using the provided SSA instance, identifier data, configuration, and action handler.
        
        Args:
            ssa_instance: The SSA instance to be used by the runtime.
            id: A dictionary containing identification details for the runtime.
            config: A dictionary with configuration settings for the runtime.
            action_handler: A callable responsible for handling actions triggered by the runtime.
        """
        raise NotImplementedError

    def launch(self, setup_func):
        """Launches the SSA runtime.
        
        Connects to the network and sends registration messages. If the connection is
        successful, it starts running registered tasks and waits for incoming messages.
        
        Args:
            setup_func: A function to initialize and register user code before the runtime starts.
        """
        raise NotImplementedError

    async def sync_property(self, property_name, value, **kwargs):
        """
        Synchronizes a property with the WoT servient.
        
        Args:
            property_name: The name of the property to update.
            value: The new value to assign to the property.
            **kwargs: Optional keyword arguments for additional synchronization parameters.
        """
        raise NotImplementedError

    async def trigger_event(self, event_name, payload, **kwargs):
        """
        Triggers an event by sending it to the WoT servient.
        
        Notifies the WoT servient of an event identified by its name and associated payload.
        Additional keyword arguments may provide runtime-specific options and are ignored
        if not recognized.
        
        Args:
            event_name: The event's name.
            payload: The data to be sent with the event.
            **kwargs: Optional runtime-specific parameters.
        
        Returns:
            True if the event was triggered successfully, False otherwise.
        """
        raise NotImplementedError

    def rt_task_create(self, task_func):
        """
        Registers a task for execution by the runtime.
        
        This method schedules the provided task function for asynchronous execution
        during the runtime's operation.
        
        Args:
            task_func: A callable representing the task to be executed.
        """
        raise NotImplementedError


    async def rt_task_sleep_ms(self, ms):
        raise NotImplementedError

    async def rt_task_report_status(self, status):
        raise NotImplementedError
