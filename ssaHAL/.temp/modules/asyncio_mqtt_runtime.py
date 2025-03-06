import json
import asyncio
from ssa.interfaces import SSARuntime
from umqtt.simple import MQTTClient


class AsyncioMQTTRuntime(SSARuntime):

    def __init__(self, ssa_instance, id, config, action_handler):
        assert isinstance(id, dict), 'ID configuration should be a dictionary'
        uuid = id.get('uuid')
        model = id.get('model')
        assert isinstance(uuid, str), 'UUID should be a string'
        assert isinstance(model, str), 'Model should be a string'
        version = id.get('version')
        assert isinstance(version, dict), 'Version should be a dictionary'
        assert isinstance(version.get('instance'), str
            ), 'instance version not found'
        assert isinstance(version.get('model'), str), 'model version not found'
        assert isinstance(config, dict
            ), 'Runtime configuration should be a dictionary'
        broker = config.get('broker')
        assert isinstance(broker, dict), 'broker config should be a dictionary'
        broker_addr = broker.get('addr')
        assert isinstance(broker_addr, str
            ), 'Broker address should be a string'
        connection_opts = config.get('connection')
        assert isinstance(connection_opts, dict
            ), 'Connection config should be a dictionary'
        self._retries = connection_opts.get('retries', 3)
        self._timeout = connection_opts.get('timeout_ms', 2000)
        self.registration_topic = f'/registration/{uuid}'
        self.registration_payload = json.dumps(id)
        self.base_topic = f'{model}/{uuid}'
        self._client = MQTTClient(uuid, broker_addr, broker.get('port', 0),
            broker.get('user'), broker.get('password'), broker.get(
            'keepalive', 0), broker.get('ssl'))
        self._clean_session = config.get('clean_session', True)
        self._action_qos = config.get('action_qos', 1)
        last_will = config.get('last_will')
        if last_will is not None:
            assert isinstance(last_will, dict
                ), 'Last will config should be a dictionary if provided'
            lw_msg = last_will.get('message')
            lw_qos = last_will.get('qos')
            lw_retain = last_will.get('retain')
            assert isinstance(lw_msg, str
                ), 'Last will message should be a string'
            assert isinstance(lw_qos, int
                ), 'Last will QoS should be an integer'
            assert isinstance(lw_retain, bool
                ), 'Last will retain flag should be a boolean'
            topic = f'{self.base_topic}/last_will'
            self._client.set_last_will(topic, lw_msg, lw_retain, lw_qos)
        assert ssa_instance is not None, 'SSA instance should not be None'
        self._ssa = ssa_instance
        self._tasks = []
        assert action_handler is not None, 'Action handler should not be None'
        self._set_global_action_handler(action_handler)

    def _set_global_action_handler(self, global_handler):
        base_action_topic = f'{self.base_topic}/actions'
        print(
            f'[INFO] Setting global action handler for topic: {base_action_topic}'
            )

        def handler_wrapper(topic: bytes, payload: bytes):
            try:
                topic = topic.decode('utf-8')
                payload = json.loads(payload.decode('utf-8'))
            except ValueError as e:
                print(f'[ERROR] Failed to decode MQTT message to JSON: {e}')
                return
            except Exception as e:
                print(f'[ERROR] Failed to decode MQTT message to utf-8: {e}')
                return
            print(f'[DEBUG] Decoded MQTT message: {topic} - {payload}')
            action_uri = topic[len(base_action_topic) + 1:]
            global_handler(action_uri, payload)
        self._action_handler = handler_wrapper

    async def _connect_to_broker(self):
        print('[INFO] Connecting to broker...')
        for i in range(self._retries):
            print(
                f'[INFO] Attempting to connect to broker (attempt {i + 1}/{self._retries})'
                )
            try:
                self._client.connect(self._clean_session, self._timeout)
                return
            except Exception as e:
                print(f'[ERROR] Failed to connect to broker: {e}')
                print(f'[INFO] Retrying in {2 ** i} seconds')
                await asyncio.sleep(2 ** i)
        raise Exception(
            f'[ERROR] Failed to connect to broker after {self._retries} retries'
            )

    async def _main_loop(self):
        self._client.set_callback(self._action_handler)
        self._client.subscribe(f'{self.base_topic}/actions/#')
        self._client.publish(self.registration_topic, self.
            registration_payload, qos=1, retain=True)
        while True:
            blocking = len(self._tasks) == 0
            if blocking:
                print('[INFO] No tasks to run. Blocking on MQTT messages.')
                self._client.wait_msg()
            else:
                self._client.check_msg()
                await asyncio.sleep_ms(200)

    async def _runtime_entry(self, main):
        if main is not None:
            try:
                main(self._ssa)
            except Exception as e:
                raise Exception(f'[WARNING] Failed to run user main: {e}'
                    ) from e
        print('[INFO] Connecting to broker...')
        try:
            await self._connect_to_broker()
            print('[INFO] Connected to broker.')
        except Exception as e:
            raise Exception(
                f'[ERROR] MQTT Runtime failed to connect to broker: {e}'
                ) from e
        try:
            await self._main_loop()
        except Exception as e:
            raise Exception(f'[ERROR] Main loop exception: {e}') from e
        print('[INFO] Main loop finished.')

    def launch(self, main=None):
        try:
            asyncio.run(self._runtime_entry(main))
        except Exception as e:
            raise Exception(f'[FATAL] Runtime exception: {e}') from e
        print('[INFO] Runtime exited.')

    async def sync_property(self, property_name, value, qos=0, retain=False,
        **_):
        try:
            topic = f'{self.base_topic}/properties/{property_name}'
            self._client.publish(topic, json.dumps(value), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to sync property '{property_name}': {e}")
            return False
        return True

    async def trigger_event(self, event_name, payload, qos=0, retain=False, **_
        ):
        try:
            topic = f'{self.base_topic}/events/{event_name}'
            self._client.publish(topic, json.dumps(payload), retain, qos)
        except Exception as e:
            print(f"[WARNING] Failed to trigger event '{event_name}': {e}")
            return False
        return True

    def rt_task_create(self, task_func, *args, **kwargs):

        async def wrapped_task():
            task_name = 'unknown' if not hasattr(task_func, '__name__'
                ) else task_func.__name__
            try:
                print(
                    f"[INFO] Starting task '{task_name}' with args: {args}, kwargs: {kwargs}"
                    )
                await task_func(self._ssa, *args, **kwargs)
                print(f"[INFO] Task '{task_name}' finished executing.")
            except Exception as e:
                print(f"[WARNING] Task '{task_name}' failed: {e}")
            finally:
                if task_func in self._tasks:
                    self._tasks.remove(task_func)
        self._tasks.append(asyncio.create_task(wrapped_task()))

    async def rt_task_sleep_ms(self, ms):
        await asyncio.sleep_ms(ms)

    async def rt_task_report_status(self, action_name, status):
        raise NotImplementedError
