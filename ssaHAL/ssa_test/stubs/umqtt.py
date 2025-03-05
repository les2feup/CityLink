import sys
from types import ModuleType

class MQTTClient():
    def __init__(self, *args, **kwargs):
        pass

    def connect(self):
        pass

    def disconnect(self):
        pass

    def publish(self, *args, **kwargs):
        pass

    def subscribe(self, *args, **kwargs):
        pass

    def check_msg(self):
        pass

    def wait_msg(self):
        pass


def load_stub():
    if "umqtt.simple" not in sys.modules:
        mqtt_stub = ModuleType("umqtt.simple")
        mqtt_stub.MQTTClient = MQTTClient
        sys.modules["umqtt.simple"] = mqtt_stub
