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

    def set_property(self, prop_name, prop_value, **kwargs):
        """
        Asynchronously set the value of a property.

        Subclasses must implement this coroutine to update the internal state
        associated with the given property name using the provided value.
        Additional keyword arguments may be used to support custom update logic.
        """
        raise NotImplementedError("Subclasses must implement set_property()")

    def emit_event(self, event_name, event_data, **kwargs):
        """
        Emit an event with the specified name and data.

        Subclasses must override this method to emit an event with the specified name and data.
        Additional keyword arguments may be used to provide further customization.
        """
        raise NotImplementedError("Subclasses must implement emit_event()")

    def sync_action(func):
        """Decorator for synchronous action handlers."""

        async def wrapper(self, *args, **kwargs):
            raise NotImplementedError("Subclasses must implement sync_action()")

        return wrapper

    def async_action(func):
        """Decorator for asynchronous action handlers."""

        async def wrapper(self, *args, **kwargs):
            raise NotImplementedError("Subclasses must implement async_action()")

        return wrapper

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

    def _invoke_action(self, action_name, action_input, **kwargs):
        """Invoke the specified action with the provided arguments."""
        raise NotImplementedError("Subclasses must implement invoke_action()")

    def _builtin_action_vfs_read(self, action_input):
        """Read the contents of a file from the virtual file system."""
        raise NotImplementedError("Subclasses must implement builtin_action_vfs_read()")

    def _builtin_action_vfs_write(self, action_input):
        """Write data to a file in the virtual file system."""
        raise NotImplementedError(
            "Subclasses must implement builtin_action_vfs_write()"
        )

    def _builtin_action_vfs_list(self, action_input):
        """List the contents of the virtual file system."""
        raise NotImplementedError("Subclasses must implement builtin_action_vfs_list()")

    def _builtin_action_vfs_delete(self, action_input):
        """Delete a file from the virtual file system."""
        raise NotImplementedError(
            "Subclasses must implement builtin_action_vfs_delete()"
        )

    def _builtin_action_reload_core(self, action_input):
        """Reload the core module."""
        raise NotImplementedError(
            "Subclasses must implement builtin_action_reload_core()"
        )

    def _builtin_action_set_property(self, action_input):
        """Set the value of a property."""
        raise NotImplementedError(
            "Subclasses must implement builtin_action_set_property()"
        )
