from ._config import ConfigLoader
from ._action_handler import ActionHandler
from ._actions import firmware_update, property_update

from .interfaces import NetworkDriver, SSARuntime

class SSA():
    """
    The SSA class is the main class for the Smart Sensor Actuator framework
    """
    def __init__(self, nic_class: NetworkDriver, runtime_class: SSARuntime):
        """
        Initializes a new SSA instance.
        
        Loads configuration from predefined JSON files and sets up the network 
        interface and runtime components using the provided driver classes.
        Also initializes the global action handler and the internal property
        storage. 

        Raises:
            Exception: Configuration loading or component initialization fails.

        Args:
            nic_class: The NetworkDriver implementation to use
            runtime_class: The SSARuntime implementation to use
        """
        config_handler = ConfigLoader(["/config/config.json",
                                       "/config/secrets.json"])
        self._action_handler = ActionHandler(self)
        try:
            # Configuration Module
            config = config_handler.load_config()
            global_handler = self._action_handler.global_handler
            self._nic = nic_class(config["network"])
            self._runtime: SSARuntime = runtime_class(self,
                                                      config["id"],
                                                      config["runtime"],
                                                      global_handler)

        except Exception as e:
            raise Exception(f"[ERROR] Failed to init SSA instance: {e}") from e

        self._properties = {}

    def launch(self, user_main=None):
        """
        Launch the SSA runtime and execute optional user code.
        
        This method registers actions for firmware and property updates, then
        launches the runtime environment using an optional user-defined 
        callback. If the runtime fails to launch, the raised exception i
        propagated with additional context. Upon successful termination,
        an informational message is printed.
        
        Args:
            user_main: Optional callback function to execute as part of the
            runtime.
        """
        try:
            #TODO: extract this into the config
            self._nic.connect(retries=5, base_timeout_ms=1000)
        except Exception as e:
            raise Exception(f"[ERROR] Failed to connect to network: {e}") from e

        self._action_handler.register_action("/ssa/firmware_update",
                                             firmware_update)
        self._action_handler.register_action("/ssa/set/{prop}",
                                             property_update)
        try:
            self._runtime.launch(user_main)
        except Exception as e:
            raise Exception(f"[ERROR] Runtime failed: {e}") from e
        print("[INFO] Runtime exited.")

    def has_property(self, name):
        """
        Check if a property with the specified name exists.
        
        Args:
            name: The name of the property.
        
        Returns:
            True if the property exists, False otherwise.
        """
        return name in self._properties

    def create_property(self, name, default):
        """
        Creates a new property with the given default value.
        
        Raises:
            Exception: If a property with the specified name already exists.
        """
        if name not in self._properties:
            self._properties[name] = default
        else:
            raise Exception(f"[ERROR] Property `{name}` already exists. \
                    Use `set_property` to change it.")

    def get_property(self, name):
        """
        Retrieves the value of the specified property.
        
        Raises:
            Exception: If the property does not exist. Use `create_property` to
            create it first.
        
        Args:
            name: The name of the property.
        
        Returns:
            The value associated with the property.
        """
        if name not in self._properties:
            raise Exception(f"[ERROR] Property `{name}` does not exist. \
                    Create it using `create_property` first.")
        return self._properties[name]

    async def set_property(self, name, value, **kwargs):
        """
        Set a property's value and synchronize it with the runtime.
        
        If the property value changes update and have the runtime synchronize it
        with the network. Additional keyword arguments are passed to the runtime
        in order to costumize the synchronization process.
        Any unrecognized keys are ignored.

        Raises:
            Exception: If the property does not exist. Use `create_property` to
            create it first.
        """
        if name not in self._properties:
            raise Exception(f"[ERROR] Property `{name}` does not exist. \
                    Create it using `create_property` first.")

        if not await self._runtime.sync_property(name, value, **kwargs):
            raise Exception(f"[ERROR] Failed to synchronize property `{name}`.")

        self._properties[name] = value

    async def trigger_event(self, name, value, **kwargs):
        """
        Triggers an event in the runtime.
        
        Forwards the event with the specified name and value to the runtime, along with any
        additional keyword arguments (unrecognized arguments are ignored).
        
        Returns:
            The result from the runtime's trigger_event operation, allowing the caller
            to handle any potential failures.
        """
        return await self._runtime.trigger_event(name, value, **kwargs)

    def register_action(self, uri_template: str, callback):
        """
        Register an action with a URI template and its callback function.
        
        This method registers a callback to be executed when an action matching the specified
        URI template is invoked by a WoT servient or other client. The URI template may include
        variables enclosed in curly braces (e.g., {var_name}). The callback function must accept
        at least two arguments: one for the action's URI and one for the payload. If the URI template
        contains variables, the callback should also accept additional arguments corresponding to
        those variables.
        
        Args:
            uri_template: A string representing the URI template, which may include variables in the
                form '{var_name}'.
            callback: A function to be executed when the action is invoked. It should accept the URI,
                payload, and additional arguments if the URI template includes variables.
        
        Example:
            uri_template = "/actions/{action_id}"
            def callback(uri, payload, action_id):
                pass

            uri_template = "/actions/{action_id}/subactions/{subaction_id}"
            def callback(uri, payload, action_id, subaction_id):
                pass
        """
        self._action_handler.register_action(uri_template, callback)

    def create_task(self, task, *args, **kwargs):
        """
        Creates a task in the runtime.
        
        Delegates task creation to the underlying runtime instance.
        
        Args:
            task: The task object to be created.
        """
        self._runtime.rt_task_create(task, *args, **kwargs)
