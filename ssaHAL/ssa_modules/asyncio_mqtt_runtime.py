import json
import asyncio
import umsgpack
from ssa.interfaces import SSARuntime
from umqtt.simple import MQTTClient 

class AsyncioMQTTRuntime(SSARuntime):
    def __init__(self, config):
        """
        Initialize an AsyncioMQTTRuntime instance with validated identity and connection settings.
        
        This constructor verifies the essential configuration for the MQTT runtime.
        It checks that the SSA instance, action handler, identity, and runtime configuration are provided and correctly structured.
        In particular, it ensures that the identity dictionary contains the required "uuid", "model", and "version"
        (with "instance" and "model" keys), and that the configuration includes valid broker details and connection options
        such as retries and timeout. It initializes MQTT topics for registration and base operations, sets up an MQTT client
        with the specified broker address, port, and credentials, and configures a last will message if provided.
        """
        self._tasks = {}

        assert isinstance(config, dict), "ID configuration should be a dictionary"

        self.id = config.get("id")
        self.model = config.get("model")
        assert isinstance(uuid, str), "UUID should be a string"
        assert isinstance(model, str), "Model should be a string" 

        self.version = config.get("version")
        assert isinstance(version, dict), "Version should be a dictionary"
        assert isinstance(version.get("instance"), str), "instance version not found"
        assert isinstance(version.get("model"), str), "model version not found"

        assert isinstance(config, dict), "Runtime configuration should be a dictionary"

        broker = config.get("broker")
        assert isinstance(broker , dict), "broker config should be a dictionary"
        broker_addr = broker.get("addr")
        assert isinstance(broker_addr, str), "Broker address should be a string"

        connection_opts = config.get("connection")
        assert isinstance(connection_opts, dict), "Connection config should be a dictionary"

        self._retries = connection_opts.get("retries", 3)
        self._timeout = connection_opts.get("timeout_ms", 2000)

        self._client = MQTTClient(uuid,
                                  broker_addr,
                                  broker.get("port", 0),
                                  broker.get("user"),
                                  broker.get("password"),
                                  broker.get("keepalive", 0),
                                  broker.get("ssl"))

        self._clean_session = config.get("clean_session", True)
        self._action_qos = config.get("action_qos", 1)

        last_will = config.get("last_will")
        if last_will is not None:
            assert isinstance(last_will, dict), "Last will config should be a dictionary if provided"
            lw_msg = last_will.get("message")
            lw_qos = last_will.get("qos")
            lw_retain = last_will.get("retain")

            assert isinstance(lw_msg, str), "Last will message should be a string"
            assert isinstance(lw_qos, int), "Last will QoS should be an integer"
            assert isinstance(lw_retain, bool), "Last will retain flag should be a boolean"

            topic = f"{self.base_topic}/last_will"
            self._client.set_last_will(topic, lw_msg, lw_retain, lw_qos)


    async def _connect_to_broker(self):
        """
        Attempts to connect to the MQTT broker with exponential backoff retries.
        
        This coroutine makes up to a configured number of connection attempts. After each
        failed attempt, it waits for an exponentially increasing delay before retrying.
        If the connection cannot be established after all retries, an Exception is raised.
        """
        print("[INFO] Connecting to broker...")
        for i in range(self._retries):
            print(f"[INFO] Attempting to connect to broker (attempt {i + 1}/{self._retries})")
            try:
                self._client.connect(self._clean_session, self._timeout)
                return
            except Exception as e:
                print(f"[ERROR] Failed to connect to broker: {e}")
                print(f"[INFO] Retrying in {2 ** i} seconds")
                await asyncio.sleep(2 ** i)

        raise Exception(f"[ERROR] Failed to connect to broker after {self._retries} retries")

    def _action_handler(self):
        pass

    async def _main_loop(self):
        """
        Runs the main MQTT loop to process incoming messages and execute tasks.
        
        Configures the MQTT client with an action callback, subscribes to the actions topic,
        and publishes the registration payload with QoS 1 and retain flag. In an infinite loop,
        if no tasks are scheduled, it blocks waiting for MQTT messages; otherwise, it checks for
        messages and yields briefly to allow task execution.
        """
        self._client.set_callback(self._action_handler)
        self._client.subscribe(f"ssa_core/{self.id}/fw", qos=1)
        self._client.publish(self.registration_topic,
                             self.registration_payload,
                             qos=1,
                             retain=True)

        while True:
            blocking = len(self._tasks) == 0
            if blocking:
                print("[INFO] No tasks to run. Blocking on MQTT messages.")
                self._client.wait_msg()
            else:
                self._client.check_msg()
                await asyncio.sleep_ms(200)

    async def _runtime_entry(self, main):
        """
        Executes user-defined setup (if provided) and starts the MQTT runtime.
        
        If a callable is provided via the 'main' parameter, it is executed with the SSA
        instance to perform any user-specific initialization. The method then attempts to
        connect to the MQTT broker and, upon a successful connection, enters the main loop
        for processing MQTT messages. Exceptions raised during the setup, connection, or
        main loop are propagated.
            
        Args:
            main: Optional callable for user-defined initialization that accepts the SSA instance.
        
        Raises:
            Exception: If the user setup, broker connection, or main loop execution fails.
        """
        if main is not None:
            try:
                main(self._ssa)
            except Exception as e:
                raise Exception(f"[WARNING] Failed to run user main: {e}") from e

        print("[INFO] Connecting to broker...")
        try:
            await self._connect_to_broker()
            print("[INFO] Connected to broker.")
        except Exception as e:
            raise Exception(f"[ERROR] MQTT Runtime failed to connect to broker: {e}")\
                    from e

        try:
            await self._main_loop()
        except Exception as e:
            raise Exception(f"[ERROR] Main loop exception: {e}") from e

        print("[INFO] Main loop finished.")

    def launch(self, main=None):
        """
        Launches the asynchronous MQTT runtime.
        
        Runs the runtime entry method in an asyncio event loop, optionally executing a
        user-defined setup function (main) before entering the main loop. Raises an exception
        if an error occurs during launch.
        
        Args:
            main: Optional function for performing user-defined initialization before the main loop.
        
        Raises:
            Exception: If launching the runtime fails, an exception is raised with a descriptive
            error message.
        """
        try:
            asyncio.run(self._runtime_entry(main))
        except Exception as e:
            raise Exception(f"[FATAL] Runtime exception: {e}")\
                    from e

        print("[INFO] Runtime exited.")

    async def sync_property(self, prop_name, prop_value, qos=1, retain=True, **_):
        """Synchronizes a property with the WoT servient.
        Publishes the given property value as a JSON payload to an MQTT topic derived from
        the base topic and the property name. Returns True if the publication is successful;
        if an exception occurs during publishing, a warning is printed and the method returns False.

        Args:
            property_name: The name identifying the property.
            value: The value to be synchronized.
            qos: The quality-of-service level for the MQTT message (default is 0).
            retain: Indicates whether the MQTT message should be retained by the broker (default is False).
            **_: Additional keyword arguments (ignored).

        Returns:
            bool: True if the property was successfully synchronized, False otherwise.
        """
        try:
            topic = f"{self.base_topic}/properties/{prop_name}"
            self._client.publish(topic, json.dumps(prop_value), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to sync property '{prop_name}': {e}")
            return False
        return True

    async def emit_event(self, event_name, event_data, qos=1, retain=True, **_):
        """
        Triggers an event by publishing the payload to the appropriate MQTT topic.

        The function formats the topic by appending the event name to the base topic under the 'events' hierarchy
        and publishes the event payload to that topic. It returns True if the event is published successfully;
        otherwise, it logs a warning and returns False.

        Args:
            event_name: The event's identifier, used to construct the topic.
            payload: The payload data to be sent with the event.
            qos: The MQTT Quality of Service level for the publish operation (default is 0).
            retain: If True, the broker will retain the published event (default is False).
            **_: Additional keyword arguments, currently ignored.

        Returns:
            True if the event was triggered successfully, False otherwise.
        """
        try:
            topic = f"{self.base_topic}/events/{event_name}"
            self._client.publish(topic, json.dumps(event_data), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to trigger event '{event_name}': {e}")
            return False
        return True

    def rt_task_create(self, task_name, task_func):
        """
        Creates and schedules an asynchronous task for the runtime.

        Wraps the provided coroutine function with error handling and executes it with
        the SSA instance as its argument. Upon completion or failure, the task is
        removed from the runtime's task list, and a corresponding message is logged.

        Args:
            task_func: An awaitable callable that accepts the SSA instance.
        """
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
                print(f"[INFO] Task '{task_name}' finished executing.")
            except Exception as e:
                print(f"[WARNING] Task '{task_name}' failed: {e}")
            finally:
                del self._tasks[task_name]
                
        self._tasks[task_name] = asyncio.create_task(wrapped_task())

    async def rt_task_sleep_ms(self, ms):
        await asyncio.sleep_ms(ms)

    async def rt_task_report_status(self, action_name, status):
        raise NotImplementedError
        
