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
        """
        Initialize the MQTT runtime with required network and broker configurations.

        This constructor validates that the provided configuration contains the necessary
        network credentials and runtime settings. It sets up internal task and property
        management, defines an asynchronous action launcher for handling runtime actions,
        and initializes the MQTT client using broker parameters. It also registers built-in
        actions for virtual file system operations (list, read, write, delete) and device
        reload.

        The configuration dictionary must include:
          - 'network': a dictionary with keys 'ssid' and 'password'.
          - 'runtime': a dictionary with:
              - 'broker': a dictionary with keys 'client_id', 'ipv4', and optionally 'port',
                'username', 'password', 'keepalive', and 'ssl'.
              - 'connection': a dictionary with keys 'retries' and 'timeout_ms'.
          - 'tm': a dictionary with a 'name' key representing the instance model.
        """
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

        self._tasks = {}
        self._properties = {}

        def action_launcher(handler, input, **kwargs):
            """
            Launches an asynchronous task for the given action handler.

            Wraps the provided asynchronous handler in a task using asyncio.create_task to execute it
            with the specified input and additional keyword arguments. Logs a debug message before launching
            the task, and any exceptions raised during execution are caught and logged as errors.
            """
            print(f"[DEBUG] Launching action '{handler.__name__}'")

            async def action_wrapper():
                """
                Wraps an action handler invocation asynchronously, catching and logging exceptions.

                This coroutine awaits a pre-defined action handler with a provided input and any
                additional keyword arguments. If the handler raises an exception during execution,
                an error message is printed.
                """
                try:
                    await handler(input, **kwargs)
                except Exception as e:
                    print(f"[ERROR] Failed to execute action: {e}")

            asyncio.create_task(action_wrapper())

        self._action_handler = ActionHandler(action_launcher)

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

        def vfs_action_wrapper(executor):
            """
            Wraps an executor function to generate an asynchronous Virtual File System action.

            Returns a coroutine that invokes the provided executor with an input, serializes its
            result with umsgpack, and publishes it to an MQTT topic for VFS reporting. If an error
            occurs during execution, an error message is printed.

            Args:
                executor (callable): Function that processes input data and returns event details.

            Returns:
                callable: An asynchronous function that performs the VFS action.
            """

            async def vfs_action(input):
                try:
                    event_data = executor(input)
                    data = umsgpack.dumps(event_data)
                    topic = f"{self._base_event_topic}/{RT_NAME}/vfs/report"
                    self._mqtt.publish(topic, data, retain=False, qos=1)
                except Exception as e:
                    print(f"[ERROR] Failed to execute VFS action: {e}")

            return vfs_action

        self._core_actions = const(
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
        """
        Validates an MQTT event topic.

        Splits the topic string by "/" and ensures that none of its segments is a reserved name, an MQTT wildcard ("#" or "+"), or the instance model name. Returns True if the topic meets these criteria, and False otherwise.

        Args:
            topic (str): The MQTT event topic to be validated.

        Returns:
            bool: True if the topic is valid, False otherwise.
        """
        topic_parts = topic.split("/")
        if any(part in RESERVED_NAMES for part in topic_parts):
            return False

        if any(part in ["#", "+"] for part in topic_parts):
            return False

        if self._instance_model_name in topic_parts:
            return False

        return True

    def _is_valid_action_uri(self, uri):
        """
        Checks whether the provided action URI is valid.

        This function is a placeholder for future URI validation logic and currently
        always returns True.

        Args:
            uri: The action URI to validate.

        Returns:
            bool: True, unconditionally.
        """
        return True  # TODO: Implement

    def _is_valid_property_name(self, name):
        """
        Determines if a property name is valid.

        This placeholder method currently returns True unconditionally. In the future,
        implement validation logic to ensure that the provided property name meets the
        required criteria.
        """
        return True  # TODO: Implement

    def _on_message(self, topic, msg):
        """
        Process an MQTT message and dispatch the corresponding action.

        This method decodes the topic and message payload, then determines whether the message
        corresponds to a core or a model-specific action based on predefined topic prefixes.
        For core actions, it schedules asynchronous execution via an internal task, whereas
        for model-specific actions it invokes a global action handler. Errors encountered during
        action execution are caught and logged, and messages received on unrecognized topics
        generate a warning.

        Args:
            topic (bytes): The MQTT topic received, encoded as bytes.
            msg (bytes): The message payload encoded with umsgpack.
        """
        topic = topic.decode("utf-8")
        action_input = umsgpack.loads(msg)
        print(f"[INFO] Received message on topic '{topic}'")

        core_action_prefix = f"{self._base_action_topic}/{RT_NAME}/"
        model_action_prefix = f"{self._base_action_topic}/{self._instance_model_name}/"

        if topic.startswith(core_action_prefix):
            action_name = topic[len(core_action_prefix) :]
            try:

                async def task_func():
                    """
                    Asynchronously executes a registered core action.

                    This coroutine retrieves the action function associated with a given action name
                    from the core action mapping and awaits its execution using the action input
                    provided from the enclosing scope.
                    """
                    await self._core_actions[action_name](action_input)

                self.task_create(action_name, task_func)
            except Exception as e:
                print(f"[ERROR] Failed to execute builtin action '{action_name}': {e}")

        elif topic.startswith(model_action_prefix):
            action_name = topic[len(model_action_prefix) :]
            try:
                self._action_handler.global_handler(action_name, action_input)
            except Exception as e:
                print(f"[ERROR] Failed to execute action '{action_name}': {e}")

        else:
            # This should not happen if subscriptions are correctly set up.
            print(f"[WARNING] Received message on unknown topic '{topic}'")

    def _reload(self, *_):
        """
        Triggers a soft reset of the device.

        Disconnects from MQTT and the network before invoking MicroPython's soft reset.
        """
        self.disconnect()
        from machine import soft_reset

        soft_reset()

    ######## SSAConnector interface methods ########

    def connect(self):
        """
        Establishes the WLAN and MQTT broker connections.

        Attempts to connect to the configured Wi-Fi network and MQTT broker using exponential
        backoff retry logic. Initializes the WLAN interface, sets up the MQTT client with the
        base topics for events, actions, and properties, configures the message callback, and
        subscribes to core action topics for VFS operations and device reload.
        """
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
            """
            Checks if the WLAN interface is connected.

            Returns True if the underlying WLAN interface reports an active connection.
            If not, raises an Exception with a message indicating failure to connect to the designated SSID.

            Raises:
                Exception: If the WLAN is not connected.
            """
            if self._wlan.isconnected():
                return True
            raise Exception(f"connecting to `{ssid}` WLAN")

        with_exponential_backoff(wlan_isconnected, retries, timeout_ms)
        print("[DEBUG]\t\t->WLAN connection established.")

        clean_session = self.config["runtime"]["broker"].get("clean_session", True)

        def mqtt_connect():
            """
            Connects to the MQTT broker using pre-configured session options.

            This method establishes a connection by invoking the MQTT client's connect method
            with a clean session flag and a timeout specified in milliseconds.
            """
            self._mqtt.connect(clean_session, timeout_ms)

        with_exponential_backoff(mqtt_connect, retries, timeout_ms)
        print("[DEBUG]\t\t->MQTT client connected.")

        base_topic = f"ssa/{self.config['runtime']['broker']['client_id']}"
        self._base_event_topic = f"{base_topic}/events"
        self._base_action_topic = f"{base_topic}/actions"
        self._base_property_topic = f"{base_topic}/properties"

        self._mqtt.set_callback(self._on_message)
        print("[DEBUG]\t\t->MQTT client callback set.")

        # Subscribe to core actions.
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/list", qos=1)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/read", qos=1)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/write", qos=1)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/vfs/delete", qos=1)
        self._mqtt.subscribe(f"{self._base_action_topic}/{RT_NAME}/reload", qos=1)
        print("[DEBUG]\t\t->Subscribed to core actions.")

    def disconnect(self):
        """
        Disconnects the WLAN network and MQTT broker connection.

        If the WLAN is connected, it first disconnects from the network before disconnecting
        from the MQTT broker.
        """
        if self._wlan.isconnected():
            self._wlan.disconnect()

        self._mqtt.disconnect()

    def register_device(self):
        """
        Publishes a device registration message to the MQTT broker.

        Serializes the device configuration's "tm" data and sends it as a retained
        message with QoS level 1 to a registration topic constructed using RT_NAME.
        An informational message is printed after publishing. Registration response
        handling is not implemented.
        """
        registration_topic = f"ssa/registration/{RT_NAME}"
        registration_data = umsgpack.dumps(self.config["tm"])
        self._mqtt.publish(registration_topic, registration_data, retain=True, qos=1)
        print("[INFO] Device registration message sent.")
        # TODO: Implement registration response handling

    ######## AffordanceHandler interface methods ########

    def create_property(self, prop_name, prop_value, **_):
        """
        Creates a new property with the specified name and value.

        Adds the property to the internal collection if the name is valid and not already in use.
        Any additional keyword arguments are ignored. Raises a ValueError if the property name is
        invalid or already exists.
        """
        if (
            self._is_valid_property_name(prop_name)
            and prop_name not in self._properties
        ):
            self._properties[prop_name] = prop_value
        else:
            raise ValueError(f"Invalid or duplicate property name: '{prop_name}'")

    def get_property(self, prop_name, **_):
        """
        Retrieves the value of a specified property.

        Returns the property's value if it exists in the registry; otherwise, raises a ValueError.

        Args:
            prop_name: The name of the property to retrieve.
            **_: Additional keyword arguments (unused).

        Returns:
            The value associated with the given property.

        Raises:
            ValueError: If the property is not found.
        """
        if prop_name in self._properties:
            return self._properties[prop_name]

        raise ValueError(f"Property '{prop_name}' not found")

    async def set_property(self, prop_name, prop_value, retain=True, qos=1, **_):
        """
        Update an existing property and publish its new value via MQTT.

        Updates the in-memory property store and sends the new value to an MQTT topic
        constructed from the base property topic, the instance model name, and the property
        name. The value is serialized using umsgpack and published with the specified
        retain and QoS settings. Raises a ValueError if the property does not exist.
        Any errors during publishing are caught and logged.
        """
        if prop_name in self._properties:
            self._properties[prop_name] = prop_value
            try:
                topic = f"{self._base_property_topic}/{self._instance_model_name}/{prop_name}"
                # TODO: add options to use a custom serializer
                data = umsgpack.dumps(prop_value)
                self._mqtt.publish(topic, data, retain=retain, qos=qos)
            except Exception as e:
                print(f"[ERROR] Failed to publish property update: {e}")
        else:
            raise ValueError(f"Property '{prop_name}' not found")

    async def emit_event(self, event_name, event_data, retain=False, qos=0, **_):
        """
        Emits an MQTT event.

        Constructs and publishes an MQTT message for the given event name and data. If the
        event name is deemed invalid by the validation helper, the function logs a warning
        and returns without emitting the event. The event data is serialized using umsgpack
        before publishing. On failure to publish the message, an error is logged.

        Parameters:
            event_name: The identifier of the event to publish.
            event_data: The payload to be sent with the event.
            retain: Optional flag indicating if the message should be retained (default is False).
            qos: Optional MQTT Quality of Service level (default is 0).
        """
        if not self._is_valid_event_topic(event_name):
            print(f"[WARNING] Invalid event name: '{event_name}'")
            return  # TODO: decide on error handling strategy

        topic = f"{self._base_event_topic}/{self._instance_model_name}/{event_name}"
        try:
            data = umsgpack.dumps(
                event_data
            )  # TODO: add options to use a custom serializer
            self._mqtt.publish(topic, data, retain=retain, qos=qos)
        except Exception as e:
            print(f"[ERROR] Failed to publish event '{event_name}': {e}")

    def register_action_handler(self, action_name, action_func, **_):
        """Register an action handler and subscribe to its corresponding MQTT topic.

        This method registers a new action so that the specified callback is invoked upon
        receiving an MQTT message for that action. It also subscribes to the MQTT topic
        constructed from the base action topic, instance model name, and action name.

        Args:
            action_name (str): The name of the action.
            action_func (callable): The callback function to execute when the action is triggered.
        """
        self._action_handler.register_action(action_name, action_func)
        self._mqtt.subscribe(
            f"{self._base_action_topic}/{self._instance_model_name}/{action_name}",
            qos=1,
        )

    ######## SSARuntime interface methods ########

    def launch(self, setup_func=None):
        """
        Launches the runtime main loop.

        If a setup function is provided, it is executed before entering the main loop; any exception
        raised during setup is re-raised with additional context. The main loop continuously monitors
        MQTT messages by blocking on incoming messages when no tasks are scheduled or by non-blocking
        checks and brief sleeps when tasks are pending.

        Args:
            setup_func (callable, optional): A function to perform initialization before starting the loop.

        Raises:
            Exception: If the setup function fails.
        """

        async def main_loop():
            """
            Run the uMQTT main loop.

            Continuously monitors for MQTT messages and scheduled tasks. When no tasks are pending,
            the loop blocks until a new message arrives; otherwise, it checks for messages and briefly yields
            control to maintain asynchronous processing.
            """
            print("[INFO] Starting uMQTT runtime main loop.")
            while True:
                blocking = len(self._tasks) == 0
                if blocking:
                    print("[INFO] Waiting for incoming messages...")
                    self._mqtt.wait_msg()
                else:
                    self._mqtt.check_msg()
                    await asyncio.sleep_ms(100)  # TODO: Tune sleep time.

        if setup_func:
            try:
                setup_func()
            except Exception as e:
                raise Exception(f"Setup function failed: {e}") from e

        print("[INFO] Starting uMQTT runtime")
        asyncio.run(main_loop())

    def task_create(self, task_id, task_func):
        """
        Registers an asynchronous task for execution.

        Wraps the given coroutine function in an asyncio task that logs its start, completion,
        cancellation, or failure, and automatically removes it from the internal registry upon termination.

        Args:
            task_id: A unique identifier for the task.
            task_func: A coroutine function to execute.
        """

        async def wrapped_task():
            """
            Executes and manages an asynchronous task's lifecycle.

            This coroutine wraps a task function by awaiting its execution, logging informational
            messages when the task is launched and completed. It logs a cancellation notice if the task
            is cancelled or a warning message if an exception occurs, and it always cleans up by
            removing the task from the internal tasks list.
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
                del self._tasks[task_id]

        self._tasks[task_id] = asyncio.create_task(wrapped_task())

    def task_cancel(self, task_id):
        """
        Cancel a registered task by its unique identifier.

        Attempts to cancel the task associated with the provided task_id asynchronously. If the task exists,
        the method awaits its cancellation. If cancellation fails or the task is not found, a warning is printed.

        Args:
            task_id: Identifier of the task to cancel.
        """
        if task_id in self._tasks:
            try:
                await self._tasks[task_id].cancel()
            except Exception as e:
                print(f"[WARNING] Failed to cancel task '{task_id}': {e}")
        else:
            print(f"[WARNING] Task '{task_id}' not found.")

    async def task_sleep_s(self, s):
        """
        Asynchronously sleep for a given number of seconds.

        Awaits the specified duration using asyncio.sleep to allow other tasks to run concurrently.

        Args:
            s: The duration to sleep, in seconds.
        """
        await asyncio.sleep(s)

    async def task_sleep_ms(self, ms):
        """
        Asynchronously sleep for a given number of milliseconds.

        Pauses the current task for the specified duration without blocking the event loop.
        """
        await asyncio.sleep_ms(ms)
