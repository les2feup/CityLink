import asyncio
from ssa.interfaces import SSARuntime

class Runtime(SSARuntime):
    def __init__(self, ssa_instance, id, config):
        keepalive = 0 if config.get("keepalive") is None \
                else config.get("keepalive")
        port = 0 if config.get("port") is None \
                else config.get("port")

        server = config.get("server")
        if server is None:
            raise Exception("Server address not found in configuration")

        self._client = UMQTTClient(id,
                                   server,
                                   port,
                                   config.get("user"),
                                   config.get("password"),
                                   keepalive,
                                   config.get("ssl"))
        
        self._clean_session = True if config.get("clean_session") is None \
                else config.get("clean_session")
        self._lw_topic = config.get("lw_topic")
        self._lw_msg = config.get("lw_msg")

        if self._lw_topic is not None:
            self._client.set_last_will(self._lw_topic, self._lw_msg)
        elif self._lw_msg is not None:
            default_topic = f"last_will/{id}"
            self._client.set_last_will(default_topic, self._lw_msg)

        self._subscription_topic = config.get("subscription_topic")
        self._connection_retries = config.get("connection_retries")
        self._connection_timeout = config.get("connection_timeout")

        self._ssa = ssa_instance

    def launch(self, setup=None):
        pass

    def sync_property(self,
                      property_name,
                      value,
                      qos=0,
                      retain=False,
                      **_):
        """Synchronize a property with the WoT servient.
        @param property_name: The name of the property.
        @param value: The value of the property.
        """
        pass

    def trigger_event(self,
                      event_name,
                      payload,
                      qos=0,
                      retain=False,
                      **_):
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
