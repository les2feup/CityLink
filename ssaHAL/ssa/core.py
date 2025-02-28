from ._utils import singleton
from ._config import ConfigLoader
from ._actions import ActionHandler
from .interfaces import NetworkDriver, SSARuntime

@singleton
class SSA():
    """The SSA class is the main class for the Smart Sensor Actuator framework
    @param NetDriver The NetworkDriver implementation to use
    @param MsgClient The MessagingClient implementation to use
    """
    def __init__(self, nic_class: NetworkDriver, runtime_class: SSARuntime):
        config_handler = ConfigLoader(["/config/config.json",
                                       "/config/secrets.json"])
        action_handler = ActionHandler(self)
        try:
            # Configuration Module
            config = config_handler.load_config()
            self._config = config["ssa"]
            self._nic = nic_class(config["network"])
            self._runtime: SSARuntime = runtime_class(self,
                                                      self.config["id"],
                                                      config["runtime"])
            self._runtime.register_action_handler(
                    self.action_handler.global_handler)

        except Exception as e:
            raise Exception(f"[ERROR] Failed to init SSA instance: {e}") from e

        self._properties = {}

    def launch(self):
        """Launch the SSA runtime by connecting to the network and sending 
        registration messages.
        if the connection is successful, the main loop is started.
        if the connection fails, the device will reset.
        if there is no user code, the device will enter boot mode and wait
        for updates.
        if user code is present, the device will run the user code.
        """
        try:
            import user.app as app
            print("[INFO] User code found. Starting application.")
            try:
                self._runtime.launch(app.main)
                print("[INFO] User code completed. Resetting device.")
            except Exception as e:
                raise Exception(f"[ERROR] User code failed: {e}") from e

        except ImportError as e:
            print("[INFO] No user code found. Waiting to receive firmware.")
            self._runtime.launch()
        except Exception as e:
            raise Exception(f"[ERROR] Launch failed: {e}") from e

     def get_property(self, name):
        """Get the value of a property
        @param name: The name of the property
        @returns: The value of the property
        """
        if name not in self._properties:
            raise Exception(f"[ERROR] Property `{name}` does not exist. \
                            Set it using `set_property` first.")
        return self._properties[name]

    def _set_and_sync_property(self, name, value, **kwargs):
        self._properties[name] = value
        self._runtime.sync_property(name, value, **kwargs)

    def set_property(self, name, value, **kwargs):
        """Set the value of a property.
        Properties are synced to the WoT servient on change.
        @param name: The name of the property
        @param value: The new value of the property
        @param kwargs: Additional arguments to pass to the runtime.
        Unkown arguments are ignored
        """
        if name not in self._properties:
            return self._set_and_sync_property(name, value, **kwargs)

        prev_value = self._properties[name]
        if prev_value != value:
            return self._set_and_sync_property(name, value, **kwargs)

    def trigger_event(self, name, value, **kwargs):
        """Trigger an event
        Properties are sent to the events uri when set
        @param name: The name of the event
        @param value: The value of the event
        @param kwargs: Additional arguments to pass to the runtime.
        Unkown arguments are ignored
        """
        self._runtime.trigger_event(name, value, **kwargs)

    def register_action(self, uri_template: str, callback):
        """Register an action to be called when invoked by the WoT servient
        or other clients. 
        @param uri_template: The URI template to register. It may contain
        URI variabled in the form of {var_name}.
        @param callback: The callback function to execute when the action is
        invoked. 
        The callback function must accept at least two arguments:
            - uri: The URI of the action
            - payload: The payload of the action
        If the uri_template contains URI variables, the callback function
        must accept the same number of arguments as the number of variables
        in the URI template.
        example:
            uri_template = "/actions/{action_id}"
            def callback(ssa_instance, payload, action_id):
                pass
        """
        self._action_handler.register_action(uri_template, callback)

    def create_task(self, name: str, task):
        """Create a task
        @param name: The name of the task
        @param task: The task to create
        """
        self._runtime.create_task(name, task)
