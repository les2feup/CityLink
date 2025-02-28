import asyncio
from ssa.interfaces import SSARuntime

class Runtime(SSARuntime):
    def __init__(self, ssa_instance, id, config):
        pass

    def launch(self, user_entry=None):
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
