from ssa.interfaces import SSARuntime
from ssa_lib.action_handler import ActionHandler

from umqtt.simple import MQTTClient
from micropython import const
from network import WLAN, STA_IF

import asyncio
import umsgpack

RT_NAME = const("umqtt_core")
RESERVED_NAMES = const(("vfs", "ssa", "events", "actions", "properties", "umqtt_core"))


class uMQTTRuntime(SSARuntime):
    def __init__(self, config):
        print("[DEBUG] Initializing uMQTT runtime...")

        extra_required_config = {
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
        }
        super().__init__(config, extra_required_config)

        print("[DEBUG]\t\t->Valid config.")

        self.tasks = {}
        self.properties = {}

        def action_laucher(handler, input, **kwargs):
            async def action_wrapper():
                try:
                    await handler(input, **kwargs)
                except Exception as e:
                    raise Exception(f"[ERROR] Failed to execute action: {e}") from e

            asyncio.create_task(action_wrapper)

        self._action_handler = ActionHandler(action_laucher)

        print("[DEBUG]\t\t->Action handler initialized.")

        broker_config = self.config["runtime"]["broker"]
        self._mqtt = MQTTClient(
            client_id=broker_config["client_id"],
            server=broker_config["ipv4"],
            port=broker_config.get("port", 1883),
            user=broker_config.get("username"),
            password=broker_config.get("password"),
            keepalive=broker_config.get("keepalive", 60),
            ssl=broker_config.get("ssl"),
        )
        print("[DEBUG]\t\t->MQTT client initialized.")

        self._instance_model_name = self.config["tm"]["name"]

        from ._core_actions import vfs_list, vfs_read, vfs_write, vfs_delete

        def vfs_action_wrapper(vfs_action):
            async def vfs_action(input_bytes):
                try:
                    input = umsgpack.loads(input_bytes)
                    event_data = vfs_action(input)
                    topic = f"{self._base_event_topic}/{RT_NAME}/vfs/report"
                    data = umsgpack.dumps(event_data)
                    self._mqtt.publish(topic, data, retain=False, qos=1)
                except Exception as e:
                    raise Exception(f"[ERROR] Failed to execute VFS action: {e}") from e

            return vfs_action

        self._builtin_actions = const(
            {
                "vfs/list": vfs_action_wrapper(vfs_list),
                "vfs/read": vfs_action_wrapper(vfs_read),
                "vfs/write": vfs_action_wrapper(vfs_write),
                "vfs/delete": vfs_action_wrapper(vfs_delete),
                "reload": lambda _: self._reload(),
            }
        )
        print("[DEBUG]\t\t->Builtin actions initialized.")

    ######## Helper methods ########

    def _is_valid_event_topic(self, topic):
        topic_parts = topic.split("/")
        if any(part in RESERVED_NAMES for part in topic_parts):
            return False

        if any(part in ["#", "+"] for part in topic_parts):
            return False

        if self._instance_model_name in topic_parts:
            return False

        return True

    def _is_valid_action_uri(self, uri):
        return True  # TODO: Implement

    def _is_valid_property_name(self, name):
        return True  # TODO: Implement

    def _on_message(self, topic, msg):
        """Handle incoming messages from the broker.
        Args:
            topic (bytes): The topic on which the message was received.
            msg (bytes): The message
        """
        topic = topic.decode("utf-8")
        print(f"[INFO] Received message on topic '{topic}'")

        core_action_prefix = f"{self._base_action_topic}/{RT_NAME}/"
        model_action_prefix = f"{self._base_action_topic}/{self._instance_model_name}/"

        if action_name.startswith(core_action_prefix):
            action_name = action_name[len(core_action_prefix) :]
            try:
                self.task_create(self._core_actions[action_name](msg))
            except Exception as e:
                print(f"[ERROR] Failed to execute builtin action '{action_name}': {e}")

        elif action_name.startswith(model_action_prefix):
            action_name = action_name[len(model_action_prefix) :]
            try:
                pass  # TODO: Implement action handler
            # self._actions[action_name](msg)
            except Exception as e:
                print(f"[ERROR] Failed to execute action '{action_name}': {e}")

        else:
            # This should not happen if subscriptions are correctly set up.
            print(f"[WARNING] Received message on unknown topic '{topic}'")

    def _reload(self, *_):
        self.disconnect()
        from machine import soft_reset

        soft_reset()

    ######## SSAConnector interface methods ########

    def connect(self):
        print("[INFO] Connecting to the network and broker...")

        """Attempt to the Edge Node's SSA IoT Connector"""
        retries = self.config["runtime"]["connection"].get("retries", 3)
        timeout_ms = self.config["runtime"]["connection"].get("timeout_ms", 1000)
        ssid = self.config["network"]["ssid"]

        self._wlan = WLAN(STA_IF)
        self._wlan.active(True)
        self._wlan.connect(ssid, self.config["network"]["password"])

        print("[DEBUG]\t\t->WLAN interface initialized.")

        from ._utils import with_exponential_backoff

        def wlan_isconnected():
            if self._wlan.isconnected():
                return True
            raise Exception(f"connecting to `{ssid}` WLAN")

        with_exponential_backoff(wlan_isconnected, retries, timeout_ms)
        print("[DEBUG]\t\t->WLAN connection established.")

        clean_session = self.config["runtime"]["broker"].get("clean_session", True)
        with_exponential_backoff(
            self._mqtt.connect(clean_session, timeout_ms), retries, timeout_ms
        )
        print("[DEBUG]\t\t->MQTT client connected.")

        base_topic = f"ssa/{self.config["runtime"]["broker"]["client_id"]}"
        self._base_event_topic = f"{base_topic}/events"
        self._base_action_topic = f"{base_topic}/actions"
        self._base_property_topic = f"{base_topic}/properties"

        self._mqtt.set_callback(self._on_message)
        print("[DEBUG]\t\t->MQTT client callback set.")

        # Subscribe to core actions.
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/list", qos=2)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/read", qos=2)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/write", qos=2)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/delete", qos=2)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/reload", qos=2)
        print("[DEBUG]\t\t->Subscribed to core actions.")

    def disconnect(self):
        """Disconnect from the network."""
        if self._wlan.isconnected():
            self._wlan.disconnect()

        self._mqtt.disconnect()

    def register_device(self):
        registration_topic = f"ssa/registration/{RT_NAME}"
        registration_data = umsgpack.dumps(self.config["tm"])
        self._mqtt.publish(registration_topic, registration_data, retain=True, qos=1)
        print("[INFO] Device registration message sent.")
        # TODO: Implement registration response handling

    ######## AffordanceHandler interface methods ########

    def create_property(self, prop_name, prop_value, **_):
        """Create a new property."""
        if _is_valid_property_name(prop_name) and prop_name not in self.properties:
            self.properties[prop_name] = prop_value
        else:
            raise ValueError(f"Invalid or duplicate property name: '{prop_name}'")

    def get_property(self, prop_name, **_):
        """Get the value of a property."""
        if prop_name in self.properties:
            return self.properties[prop_name]

        raise ValueError(f"Property '{prop_name}' not found")

    async def set_property(self, prop_name, prop_value, retain=True, qos=1, **_):
        """Set the value of a property."""
        if prop_name in self.properties:
            self.properties[prop_name] = prop_value
            try:
                topic = f"{self._base_property_topic}/{self._instance_model_name}/{prop_name}"
                self._mqtt.publish(topic, prop_value, retain=retain, qos=qos)
            except Exception as e:
                print(f"[ERROR] Failed to publish property update: {e}")
        else:
            raise ValueError(f"Property '{prop_name}' not found")

    async def emit_event(self, event_name, event_data, retain=False, qos=0, **_):
        if not self._is_valid_event_topic(event_name):
            print(f"[WARNING] Invalid event name: '{event_name}'")
            return  # TODO: decide on error handling strategy

        topic = f"{self._base_event_topic}/{self._instance_model_name}/{event_name}"
        try:
            self._mqtt.publish(topic, event_data, retain=retain, qos=qos)
        except Exception as e:
            print(f"[ERROR] Failed to publish event '{event_name}': {e}")

    def register_action_handler(self, action_name, action_func, **_):
        """Register a new action."""
        self._action_handler.register_action(action_name, action_func)

    ######## SSARuntime interface methods ########

    def launch(self, setup_func=None):
        """Launch the runtime main loop. Start listening for actions and run created tasks."""

        async def main_loop():
            """Run the uMQTT runtime."""
            while True:
                blocking = len(self.tasks) == 0
                if blocking:
                    self._mqtt.wait_msg()
                else:
                    self._mqtt.check_msg()
                    await asyncio.sleep_ms(100)  # TODO: Tune sleep time.

        if setup_func:
            try:
                setup_func()
            except Exception as e:
                raise Exception(
                    f"Setup function `{setup_func.___name__}` failed: {e}"
                ) from e

        print("[INFO] Starting uMQTT runtime")
        asyncio.run(main_loop())

    def task_create(self, task_id, task_func):
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
                print(f"[INFO] Launching '{task_id}' task.")
                await task_func()
                print(f"[INFO] Task '{task_id}' finished executing.")
            except asyncio.CancelledError:
                print(f"[INFO] Task '{task_id}' was cancelled.")
            except Exception as e:
                print(f"[WARNING] Task '{task_id}' failed: {e}")
            finally:
                del self._tasks[task_name]

        self._tasks[task_id] = asyncio.create_task(wrapped_task())

    def task_cancel(self, task_id):
        """Cancel a previously registered task."""
        if task_id in self._tasks:
            try:
                self._tasks[task_id].cancel()
            except Exception as e:
                print(f"[WARNING] Failed to cancel task '{task_id}': {e}")
        else:
            print(f"[WARNING] Task '{task_id}' not found.")

    async def task_sleep_s(self, s):
        """Sleep for a given number of seconds."""
        await asyncio.sleep(s)

    async def task_sleep_ms(self, ms):
        """Sleep for a given number of milliseconds."""
        await asyncio.sleep_ms(ms)
