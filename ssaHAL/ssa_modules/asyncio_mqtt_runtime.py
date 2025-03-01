import asyncio
import json
from ssa.interfaces import SSARuntime
from umqtt.simple import MQTTClient 

class AsyncioMQTTRuntime(SSARuntime):
    def __init__(self, ssa_instance, id, config, action_handler):
        assert ssa_instance is not None, "SSA instance should not be None"
        self._ssa= ssa_instance
        self._tasks = []

        assert action_handler is not None, "Action handler should not be None"
        self._action_handler = action_handler

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

    async def _connect_to_broker(self):
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

    async def runtime_entry(self, main):
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
            raise Exception(f"[ERROR] MQTT Runtime failed to connect\
                    to broker: {e}") from e

        try:
            await self._main_loop()
        except Exception as e:
            raise Exception(f"[ERROR] Main loop failed: {e}") from e

    def launch(self, main=None):
        try:
            asyncio.run(self.runtime_entry(main))
        except Exception as e:
            raise Exception(f"[ERROR] Failed to launch runtime: {e}")\
                    from e

    def sync_property(self,
                      property_name,
                      value,
                      qos=0,
                      retain=False,
                      **_):
        """Synchronize a property with the WoT servient.
        @param property_name: The name of the property.
        @param value: The value of the property.
        @param qos: The QoS level to use when sending the property.
        @param retain: Whether the property should be retained by the broker.

        @return True if the property was synced successfully, False otherwise.
        """
        try:
            topic = f"{self.base_topic}/properties/{property_name}"
            self._client.publish(topic, json.dumps(value), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to sync property '{property_name}': {e}")
            return False
        return True

    def trigger_event(self,
                      event_name,
                      payload,
                      qos=0,
                      retain=False,
                      **_):
        """Trigger an event, sending it to the WoT servient.
        @param event_name: The name of the event.
        @param payload: The payload of the event.
        @param qos: The QoS level to use when sending the event.
        @param retain: Whether the event should be retained by the broker.

        @return True if the event was triggered successfully, False otherwise.
        """
        try:
            topic = f"{self.base_topic}/events/{event_name}"
            self._client.publish(topic, json.dumps(payload), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to trigger event '{event_name}': {e}")
            return False
        return True

    def create_task(self, task_func):
        """Create a task to be executed by the runtime.
        @param task_func: The function to execute.
        """
        assert task_func is not None, "Task function should not be None"
        async def wrapped_task():
            try:
                await task_func(self._ssa)
                print(f"[INFO] Task '{task_func.__name__}' finished executing.")
            except Exception as e:
                print(f"[WARNING] Task '{task_func.__name__}' failed: {e}")
            finally:
                if task_func in self._tasks:
                    self._tasks.remove(task_func)

        self._tasks.append(asyncio.create_task(wrapped_task()))
