from ssa.interfaces import SSARuntime

from umqtt.simple import MQTTClient
from network import WLAN, STA_IF
from micropython import const

import asyncio
import umsgpack

RT_NAME = const("umqtt_core")
REGISTRATION_TOPIC = const("ssa/umqtt_core/registration")

RESERVED_NAMES = const(["vfs",
                        "ssa",
                        "events",
                        "actions",
                        "properties",
                        "umqtt_core"])

EXTRA_REQUIRED_CONFIG = const({
        "network": {
            "ssid": str,
            "password": str,
            },
        "runtime": {
            "broker": {
                "client_id": str,
                "ipv4": str,
                },
            "connection": {
                "retries": int,
                "timeout_ms": int,
                },
            },
    })

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
        super().__init__(config, EXTRA_REQUIRED_CONFIG)

        broker_config = config["runtime"]["broker"]
        self._mqtt = MQTTClient(
            client_id=broker_config["client_id"],
            server=broker_config["broker"]["ipv4"],
            port=broker_config["broker"].get("port", 1883),
            user=broker_config.get("username"),
            password=broker_config.get("password"),
            keepalive=broker_config.get("keepalive", 60),
            ssl=broker_config.get("ssl"))

    ######## SSAConnector interface methods ######## 
    async def connect(self):
        """Attempt to the Edge Node's SSA IoT Connector"""
        retries = self.config["runtime"]["connection"].get("retries", 3)
        timeout_ms = self.config["runtime"]["connection"].get("timeout_ms", 1000)
        ssid = self.config["network"]["ssid"]

        self._wlan = WLAN(STA_IF)
        self._wlan.active(True)
        self._wlan.connect(ssid, self.config["network"]["password"])

        async def wlan_isconnected():
            if self._wlan.isconnected():
                return True
            raise Exception(f"connecting to `{ssid}` WLAN")

        await _with_exponential_backoff(wlan_isconnected, retries, timeout_ms)

        cleanup_session = self.config["runtime"]["broker"].get("clean_session", True)

        await _with_exponential_backoff(self._mqtt.connect(clean_session, 
                                                           timeout_ms),
                                        retries, timeout_ms)

        base_topic = f"ssa/{self.config["runtime"]["broker"]["client_id"]}"

        self._base_event_topic = f"{base_topic}/events"
        self._base_action_topic = f"{base_topic}/actions"
        self._base_property_topic = f"{base_topic}/properties"

        core_vfs_action_topic = f"{self._base_action_topic}/{RT_NAME}/vfs"
        core_reload_action_topic = f"{self._base_action_topic}/{RT_NAME}/reload"

        self._mqtt.set_callback(self._on_message)
        self._mqtt.subscribe(core_vfs_action_topic, qos=1)
        self._mqtt.subscribe(core_reload_action_topic, qos=1)

    async def disconnect(self):
        """Disconnect from the network."""
        if self._wlan.isconnected():
            self._wlan.disconnect()

        self._mqtt.disconnect()

    async def register_device(self):
        registration_data = umsgpack.dumps(self.config["tm"])
        self._mqtt.publish(REGISTRATION_TOPIC, registration_data)
        # TODO: Implement registration response handling


    ######## AffordanceHandler interface methods ######## 

    """Base class defining the AffordanceHandler interface."""
    def __init__(self, config):
        """Initialize the AffordanceHandler base class."""

    def create_property(self, prop_name, prop_value, **kwargs):
        """Create a new property."""
        raise NotImplementedError("Subclasses must implement create_property()")

    def get_property(self, prop_name, **kwargs):
        """Get the value of a property."""
        raise NotImplementedError("Subclasses must implement get_property()")

    async def set_property(self, prop_name, prop_value, **kwargs):
        """Set the value of a property."""
        raise NotImplementedError("Subclasses must implement set_property()")

    async def emit_event(self, event_name, event_data, **kwargs):
        """Publish an event to all subscribers."""
        raise NotImplementedError("Subclasses must implement emit_event()")

    def register_action_handler(self, action_name, action_func, **kwargs):
        """Register a new action."""
        raise NotImplementedError("Subclasses must implement register_action()")

    ######## SSARuntime interface methods ######## 
    def _on_message(self, topic, msg):
        pass

    async def _run(self):
        """Run the uMQTT runtime."""

        while True:
            blocking = len(self._tasks) == 0
            if blocking:
                print("[INFO] No tasks to run. Blocking on MQTT messages.")
                self._client.wait_msg()
            else:
                self._client.check_msg()
                await asyncio.sleep_ms(100)
            

    def launch(self, extra_init_func=None):
        """Launch the runtime.

        Args:
            extra_init_func (function): An optional function to run before the runtime
            is started.
        """
        if extra_init_func:
            try:
                extra_init_func()
            except Exception as e:
                print(f"[ERROR] Extra initialization function `{extra_init_func.__name__}`failed: {e}")

        print("[INFO] Starting uMQTT runtime")
        asyncio.run(self._run())

    def rt_task_create(self, task_id, task_func):
        """Register a task for execution."""

        async def wrapped_task():
            """
            Wraps a task function for asynchronous execution.

            Awaits the provided task function using an SSA instance and logs its outcome.
            If the task completes successfully, an informational message is printed;
            if it raises an exception, a warning is printed.
            In all cases, the task is removed from the internal tasks list upon completion.
            """
            try:
                await task_func()
                print(f"[INFO] Task '{task_id}' finished executing.")
            except asyncio.CancelledError:
                print(f"[INFO] Task '{task_id}' was cancelled.")
            except Exception as e:
                print(f"[WARNING] Task '{task_id}' failed: {e}")
            finally:
                del self._tasks[task_name]

        self._tasks[task_id] = asyncio.create_task(wrapped_task())

    def rt_task_cancel(self, task_id):
        """Cancel a previously registered task."""
        if task_id in self._tasks:
            try:
                self._tasks[task_id].cancel()
            except Exception as e:
                print(f"[WARNING] Failed to cancel task '{task_id}': {e}")
        else:
            print(f"[WARNING] Task '{task_id}' not found.")

    async def rt_task_sleep_s(self, s):
        """Sleep for a given number of seconds."""
        await asyncio.sleep(s)

    async def rt_task_sleep_ms(self, ms):
        """Sleep for a given number of milliseconds."""
        await asyncio.sleep_ms(ms)
