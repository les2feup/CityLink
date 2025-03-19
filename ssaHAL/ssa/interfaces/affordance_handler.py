class AffordanceHandler:
    """Base class defining the AffordanceHandler interface."""

    def __init__(self, config):
        """
        Initialize the affordance handler with the specified configuration.
        
        Subclasses must override this method to perform any necessary initialization
        using the provided configuration settings.
        """
        raise NotImplementedError("Subclasses must implement __init__()")

    def create_property(self, prop_name, prop_value, **kwargs):
        """
        Create a new property.
        
        This abstract method defines the interface for adding a new property identified by its name and value.
        Subclasses must override this method to implement the specific creation logic. Additional keyword arguments
        can be used to provide further customization.
        
        Raises:
            NotImplementedError: Always, as this method is intended to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement create_property()")

    def get_property(self, prop_name, **kwargs):
        """
        Retrieve the value of a specified property.
        
        Subclasses must override this method to return the current value associated with the provided property name. Additional keyword arguments may be used to support custom retrieval logic.
        """
        raise NotImplementedError("Subclasses must implement get_property()")

    async def set_property(self, prop_name, prop_value, **kwargs):
        """
        Asynchronously set the value of a property.
        
        Subclasses must implement this coroutine to update the internal state
        associated with the given property name using the provided value.
        Additional keyword arguments may be used to support custom update logic.
        """
        raise NotImplementedError("Subclasses must implement set_property()")

    async def emit_event(self, event_name, event_data, **kwargs):
        """Emit an event to all subscribers.
        
        This asynchronous method broadcasts an event identified by its name along with
        associated event data. Additional keyword arguments may provide subclass-specific
        options for event handling.
        
        Parameters:
            event_name: Identifier for the event to be emitted.
            event_data: Payload or details associated with the event.
            **kwargs: Optional keyword arguments for customization.
        
        Raises:
            NotImplementedError: Always raised to enforce implementation in subclasses.
        """
        raise NotImplementedError("Subclasses must implement emit_event()")

    def register_action_handler(self, action_name, action_func, **kwargs):
        """
        Registers a new action handler.
        
        Args:
            action_name (str): The identifier of the action.
            action_func (callable): The function to execute for the action.
            **kwargs: Additional keyword arguments for subclass-specific options.
        
        Raises:
            NotImplementedError: Always raised as this method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement register_action()")
