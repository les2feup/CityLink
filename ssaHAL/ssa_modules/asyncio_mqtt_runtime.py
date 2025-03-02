import json
import asyncio
from ssa.interfaces import SSARuntime
from umqtt.simple import MQTTClient 

class AsyncioMQTTRuntime(SSARuntime):
    def __init__(self, ssa_instance, id, config, action_handler):
        """
        Initialize an AsyncioMQTTRuntime instance with validated identity and connection settings.
        
        This constructor verifies the essential configuration for the MQTT runtime. It checks that the SSA instance, action handler, identity, and runtime configuration are provided and correctly structured. In particular, it ensures that the identity dictionary contains the required "uuid", "model", and "version" (with "instance" and "model" keys), and that the configuration includes valid broker details and connection options such as retries and timeout. It initializes MQTT topics for registration and base operations, sets up an MQTT client with the specified broker address, port, and credentials, and configures a last will message if provided.
        """

        assert id is not None, "ID configuration should not be None"
        assert isinstance(id, dict), "ID configuration should be a dictionary"

        uuid = id.get("uuid")
        assert uuid is not None, "UUID not found in configuration"
        model = id.get("model")
        assert model is not None, "Model not found in configuration"

        version = id.get("version")
        assert version is not None, "Version not found in configuration"
        assert isinstance(version, dict), "Version should be a dictionary"
        assert version.get("instance") is not None, "instance version not found"
        assert version.get("model") is not None, "model version not found"

        assert config is not None, "Runtime configuration should not be None"
        assert isinstance(config, dict), "Runtime configuration should\
                be a dictionary"

        broker = config.get("broker")
        assert broker is not None, "broker config not found"
        assert isinstance(broker , dict), "broker config should be a dictionary"

        broker_addr = broker.get("addr")
        assert broker_addr is not None, "broker address not found"

        broker_port = 0 if broker.get("port") is None else broker.get("port")
        keepalive = 0 if broker.get("keepalive") is None \
                else broker.get("keepalive")

        connection_opts = config.get("connection")
        assert connection_opts is not None, "Connection config not found"
        assert isinstance(connection_opts, dict), "Connection config should\
                be a dictionary"

        self._retries = connection_opts.get("retries")
        self._timeout = connection_opts.get("timeout_ms")
        assert self._retries is not None, "Retries not found in connection config"
        assert self._timeout is not None, "Timeout not found in connection config"

        self.registration_topic = f"/registration/{uuid}"
        self.registration_payload = json.dumps(id)

        self.base_topic = f"{model}/{uuid}"
        self._client = MQTTClient(uuid,
                                  broker_addr,
                                  broker_port,
                                  broker.get("user"),
                                  broker.get("password"),
                                  keepalive,
                                  broker.get("ssl"))

        self._clean_session = True if config.get("clean_session") is None \
                else config.get("clean_session")
        self._action_qos = 0 if config.get("action_qos") is None \
                else config.get("action_qos")

        last_will = config.get("last_will")
        if last_will is not None:
            lw_msg = last_will.get("message")
            lw_qos = last_will.get("qos")
            lw_retain = last_will.get("retain")

            assert lw_msg is not None, "Last will message not found"
            assert lw_qos is not None, "Last will QoS not found"
            assert lw_retain is not None, "Last will retain not found"

            topic = f"{self.base_topic}/last_will"
            self._client.set_last_will(topic, lw_msg, lw_retain, lw_qos)

        assert ssa_instance is not None, "SSA instance should not be None"
        self._ssa= ssa_instance
        self._tasks = []

        assert action_handler is not None, "Action handler should not be None"
        self._set_global_action_handler(action_handler)

    def _set_global_action_handler(self, global_handler):
        base_action_topic = f"{self.base_topic}/actions"
        print(f"[INFO] Setting global action handler for topic: {base_action_topic}")

        def handler_wrapper(topic: bytes, payload: bytes):
            """
            Wrapper function to handle incoming MQTT messages.
            
            This function is invoked by the MQTT client when a message is received.
            It decodes the topic and payload, then forwards the message to the global
            action handler for processing.
            
            Args:
                topic: The MQTT topic where the message was received.
                payload: The message payload as a byte string.
            """

            try:
                topic = topic.decode("utf-8")
                payload = payload.decode("utf-8")
            except Exception as e:
                print(f"[ERROR] Failed to decode MQTT message to utf-8: {e}")
                return

            print(f"[DEBUG] Decoded MQTT message: {topic} - {payload}")

            # subtract the base topic from the topic
            action_uri = topic[len(base_action_topic) + 1:]
            global_handler(action_uri, payload)

        self._action_handler = handler_wrapper

    async def _connect_to_broker(self):
        """
        Attempts to connect to the MQTT broker with exponential backoff retries.
        
        This coroutine makes up to a configured number of connection attempts. After each
        failed attempt, it waits for an exponentially increasing delay before retrying.
        If the connection cannot be established after all retries, an Exception is raised.
        """
        print("[INFO] Connecting to broker...")
        for i in range(self._retries):
            print(f"[INFO] Attempting to connect to broker \
                    (attempt {i + 1}/{self._retries})")
            try:
                self._client.connect(self._clean_session, self._timeout)
                return
            except Exception as e:
                print(f"[ERROR] Failed to connect to broker: {e}")
                print(f"[INFO] Retrying in {2 ** i} seconds")
                await asyncio.sleep(2 ** i)

        raise Exception(f"[ERROR] Failed to connect to broker after\
                {self._retries} retries")

    async def _main_loop(self):
        """
        Runs the main MQTT loop to process incoming messages and execute tasks.
        
        Configures the MQTT client with an action callback, subscribes to the actions topic,
        and publishes the registration payload with QoS 1 and retain flag. In an infinite loop,
        if no tasks are scheduled, it blocks waiting for MQTT messages; otherwise, it checks for
        messages and yields briefly to allow task execution.
        """
        self._client.set_callback(self._action_handler)
        self._client.subscribe(f"{self.base_topic}/actions/#")
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
                raise Exception(f"[ERROR] Failed to run user setup: {e}") \
                        from e

        print("[INFO] Running runtime main loop.")
        try:
            await self._connect_to_broker()
            print("[INFO] Connected to broker.")
        except Exception as e:
            raise Exception(f"[ERROR] MQTT Runtime failed to connect to broker: {e}")\
                    from e

        try:
            await self._main_loop()
        except Exception as e:
            raise Exception(f"[ERROR] Main loop failed: {e}") from e

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

    def sync_property(self, property_name, value, qos=0, retain=False, **_):
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
            topic = f"{self.base_topic}/properties/{property_name}"
            self._client.publish(topic, json.dumps(value), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to sync property '{property_name}': {e}")
            return False
        return True

    def trigger_event(self, event_name, payload, qos=0, retain=False, **_):
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
            self._client.publish(topic, json.dumps(payload), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to trigger event '{event_name}': {e}")
            return False
        return True

    def create_task(self, task_func):
        """
        Creates and schedules an asynchronous task for the runtime.

        Wraps the provided coroutine function with error handling and executes it with
        the SSA instance as its argument. Upon completion or failure, the task is
        removed from the runtime's task list, and a corresponding message is logged.

        Args:
            task_func: An awaitable callable that accepts the SSA instance.
        """
        assert task_func is not None, "Task function should not be None"
        async def wrapped_task():
            """
            Wraps a task function for asynchronous execution.

            Awaits the provided task function using an SSA instance and logs its outcome.
            If the task completes successfully, an informational message is printed;
            if it raises an exception, a warning is printed.
            In all cases, the task is removed from the internal tasks list upon completion.
            """
            try:
                await task_func(self._ssa)
                print(f"[INFO] Task '{task_func.__name__}' finished executing.")
            except Exception as e:
                print(f"[WARNING] Task '{task_func.__name__}' failed: {e}")
            finally:
                if task_func in self._tasks:
                    self._tasks.remove(task_func)

        self._tasks.append(asyncio.create_task(wrapped_task()))
