class NetworkDriver:

    def __init__(self, config):
        raise NotImplementedError

    def connect(self, retries, base_timeout_ms, **kwargs):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def get_ip(self):
        raise NotImplementedError


class SSARuntime:

    def __init__(self, ssa_instance, id, config, action_handler):
        raise NotImplementedError

    def launch(self, setup_func):
        raise NotImplementedError

    async def sync_property(self, property_name, value, **kwargs):
        raise NotImplementedError

    async def trigger_event(self, event_name, payload, **kwargs):
        raise NotImplementedError

    def rt_task_create(self, task_func):
        raise NotImplementedError

    async def rt_task_sleep_ms(self, ms):
        raise NotImplementedError

    async def rt_task_report_status(self, status):
        raise NotImplementedError
