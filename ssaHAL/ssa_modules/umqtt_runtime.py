from ssa.interfaces import SSARuntime

from umqtt.simple import MQTTClient
from micropython import const

import asyncio
import umsgpack

REGISTRATION_TOPIC = const("ssa_core/register")

async def _with_exponential_backoff(func, retries, base_timeout_ms):
    for i in range(retries):
        retry_timeout = base_timeout_ms * (2 ** i)
        print(f"[INFO] Trying {func.__name__} (attempt {i + 1}/{retries})")
        try:
            return await func()
        except Exception as e:
            print(f"[ERROR] {func.__name__} failed: {e}, retrying in {retry_timeout} milliseconds")
            await asyncio.sleep_ms(retry_timeout)

    raise Exception(f"[ERROR] {func.__name__} failed after {retries} retries")

class uMQTTRuntime(SSARuntime):

    def __init__(self, config):
        super().__init__(config)

        runtime_config = config["runtime"]
        self._mqtt = MQTTClient(
            client_id=runtime_config.get("client_id"),
            server=runtime_config["broker_addr"],
            user=runtime_config.get("username"),
            password=runtime_config.get("password"),
            keepalive=runtime_config.get("keepalive", 60),
            ssl=runtime_config.get("ssl"))

    ######## SSAConnector interface methods ######## 

    async def connect(self, retries, base_timeout_ms):
        """Attempt to the Edge Node's SSA IoT Connector"""
        ... # connect WLAN

        mqtt_timeout = self.config["runtime"].get("mqtt_timeout", 10)
        cleanup_session = self.config["runtime"].get("clean_session", True)

        await _with_exponential_backoff(self._mqtt.connect(clean_session, mqtt_timeout),
                                        retries, base_timeout_ms)



    async def disconnect(self):
        """Disconnect from the network."""
        raise NotImplementedError("Subclasses must implement disconnect()")

    async def register_device(self):
        """Register the device with the WoT servient."""
        raise NotImplementedError("Subclasses must implement register_device()")

    async def model_update_handler(self, update_data):
        """Handle updates to the device model."""
        raise NotImplementedError("Subclasses must implement model_update_handler()")

    ######## SSARuntime interface methods ######## 

    def launch(self, extra_init_func=None):
        """Launch the runtime."""
        raise NotImplementedError("Subclasses must implement launch()")

    async def publish_property(self, prop_name, prop_value, **kwargs):
        """Publish the value of an observable property."""
        raise NotImplementedError("Subclasses must implement publish_property()")

    async def send_property(self, prop_name, prop_value, **kwargs):
        """Send a property update to a specific destination."""
        raise NotImplementedError("Subclasses must implement send_property()")

    async def emit_event(self, event_name, event_data, **kwargs):
        """Publish an event to all subscribers."""
        raise NotImplementedError("Subclasses must implement emit_event()")

    def rt_task_create(self, task_id, task_func):
        """Register a task for execution."""
        raise NotImplementedError("Subclasses must implement rt_task_create()")

    def rt_task_cancel(self, task_id):
        """Cancel a previously registered task."""
        raise NotImplementedError("Subclasses must implement rt_task_cancel()")

    async def rt_task_sleep_s(self, s):
        """Sleep for a given number of seconds."""
        raise NotImplementedError("Subclasses must implement rt_task_sleep_s()")

    async def rt_task_sleep_ms(self, ms):
        """Sleep for a given number of milliseconds."""
        raise NotImplementedError("Subclasses must implement rt_task_sleep_ms()")

