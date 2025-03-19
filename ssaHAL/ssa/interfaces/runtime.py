from .connector import SSAConnector
from .affordance_handler import AffordanceHandler


class SSARuntime(SSAConnector, AffordanceHandler):
    """Base class defining the SSARuntime interface."""

    def __init__(self, config, extra_config_template={}):
        """
        Initializes an SSARuntime instance with a validated configuration.
        
        Merges a default configuration template with any provided additional template and
        validates that the resulting configuration dictionary adheres to the expected
        structure. The configuration must be a dictionary and include required nested
        keys (such as a 'tm' key with a nested 'name' and a 'version' dictionary containing
        'model' and 'instance'). Raises a ValueError for missing keys or if the config is
        not a dictionary, and a TypeError if any value does not match the expected type.
        
        Parameters:
            config: The configuration dictionary to validate.
            extra_config_template: An optional dictionary of extra validation rules that is
                merged with the default template (default is an empty dictionary).
        """
        self.config = config

        default_config_template = {
            "tm": {"name": str, "version": {"model": str, "instance": str}}
        }

        extra_config_template.update(default_config_template)

        def validate_configuration(template, provided, path="config"):
            """
            Validates that the given configuration matches the expected template.
            
            This function recursively verifies that all required keys specified in the template are present
            in the provided configuration and that their values are of the expected types. If the expected
            type for a key is a dictionary, the corresponding sub-configuration is recursively validated.
            
            Parameters:
                template: A dictionary mapping keys to expected types or nested templates.
                provided: The configuration dictionary to validate.
                path: The current path in the configuration (used in error messages), defaults to "config".
            
            Raises:
                ValueError: If the provided configuration is not a dictionary or if a required key is missing.
                TypeError: If a configuration value does not match the expected type.
            """
            if not isinstance(provided, dict):
                raise ValueError(f"{path} must be a dictionary")

            for key, expected_type in template.items():
                if key not in provided:
                    raise ValueError(f"Missing required key: {path}['{key}']")

                if isinstance(expected_type, dict):
                    validate_configuration(
                        expected_type, provided[key], f"{path}['{key}']"
                    )

                elif not isinstance(provided[key], expected_type):
                    raise TypeError(
                        f"Expected {path}['{key}'] to be {expected_type.__name__}, "
                        f"but got {type(provided[key]).__name__}"
                    )

        validate_configuration(extra_config_template, config)

    def launch(self, setup_func=None):
        """
        Launch the runtime, optionally executing a setup function.
        
        This method initiates the runtime and is intended to be overridden by subclasses.
        If a setup function is provided, it can be used to perform any custom initialization
        or configuration prior to launch. Calling this base implementation will always raise
        NotImplementedError.
        
        Args:
            setup_func (callable, optional): A function to run for additional setup before launch.
        
        Raises:
            NotImplementedError: Always raised in this base implementation.
        """
        raise NotImplementedError("Subclasses must implement launch()")

    def task_create(self, task_id, task_func):
        """
        Register a task for execution.
        
        Associates a unique task identifier with a callable that encapsulates the task's logic.
        Subclasses must override this method to provide the actual task scheduling or execution
        mechanism.
        
        Args:
            task_id: A unique identifier for the task.
            task_func: A callable implementing the task's functionality.
        
        Raises:
            NotImplementedError: Always, as this method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement rt_task_create()")

    def task_cancel(self, task_id):
        """Cancel a registered task.
        
        Cancel the task identified by the given task_id. This method serves as a stub and must be overridden by subclasses to implement task cancellation. Calling this method directly will raise a NotImplementedError.
        
        Args:
            task_id: The identifier of the task to cancel.
        """
        raise NotImplementedError("Subclasses must implement rt_task_cancel()")

    async def task_sleep_s(self, s):
        """Asynchronously sleep for the specified number of seconds.
        
        This abstract method must be implemented by subclasses to pause
        execution asynchronously for the given duration.
        
        Args:
            s (int | float): The sleep duration in seconds.
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement rt_task_sleep_s()")

    async def task_sleep_ms(self, ms):
        """
        Asynchronously pause execution for a specified number of milliseconds.
        
        This coroutine should suspend execution for the provided duration. Subclasses 
        must override this method to implement the actual sleep behavior.
        
        Args:
            ms: Duration to sleep in milliseconds.
        
        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement rt_task_sleep_ms()")
