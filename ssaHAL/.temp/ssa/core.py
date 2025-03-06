from ._config import ConfigLoader
from ._action_handler import ActionHandler
from ._actions import firmware_update, property_update
from .interfaces import NetworkDriver, SSARuntime


class SSA:

    def __init__(self, nic_class: NetworkDriver, runtime_class: SSARuntime):
        config_handler = ConfigLoader(['/config/config.json',
            '/config/secrets.json'])
        self._action_handler = ActionHandler(self)
        try:
            config = config_handler.load_config()
            global_handler = self._action_handler.global_handler
            self._nic = nic_class(config['network'])
            self._runtime: SSARuntime = runtime_class(self, config['id'],
                config['runtime'], global_handler)
        except Exception as e:
            raise Exception(f'[ERROR] Failed to init SSA instance: {e}') from e
        self._properties = {}

    def launch(self, user_main=None):
        try:
            self._nic.connect(retries=5, base_timeout_ms=1000)
        except Exception as e:
            raise Exception(f'[ERROR] Failed to connect to network: {e}'
                ) from e
        self._action_handler.register_action('ssa/firmware_update',
            firmware_update)
        self._action_handler.register_action('ssa/set/{prop}', property_update)
        try:
            self._runtime.launch(user_main)
        except Exception as e:
            raise Exception(f'[ERROR] Runtime failed: {e}') from e
        print('[INFO] Runtime exited.')

    def has_property(self, name):
        return name in self._properties

    def create_property(self, name, default):
        if name not in self._properties:
            self._properties[name] = default
        else:
            raise Exception(
                f'[ERROR] Property `{name}` already exists.                     Use `set_property` to change it.'
                )

    def get_property(self, name):
        if name not in self._properties:
            raise Exception(
                f'[ERROR] Property `{name}` does not exist.                     Create it using `create_property` first.'
                )
        return self._properties[name]

    async def set_property(self, name, value, **kwargs):
        if name not in self._properties:
            raise Exception(
                f'[ERROR] Property `{name}` does not exist.                     Create it using `create_property` first.'
                )
        if not await self._runtime.sync_property(name, value, **kwargs):
            raise Exception(f'[ERROR] Failed to synchronize property `{name}`.'
                )
        self._properties[name] = value

    async def trigger_event(self, name, value, **kwargs):
        return await self._runtime.trigger_event(name, value, **kwargs)

    def register_action(self, uri_template: str, callback):
        self._action_handler.register_action(uri_template, callback)

    def create_task(self, task, *args, **kwargs):
        self._runtime.rt_task_create(task, *args, **kwargs)
