import sys
from types import ModuleType


class WLAN:
    def __init__(self, *args, **kwargs):
        pass

    def active(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass

    def is_connected(self, *args, **kwargs):
        pass

    def disconnect(self, *args, **kwargs):
        pass

    def ifconfig(self, *args, **kwargs):
        pass


def load_stub():
    if "network" not in sys.modules:
        network_stub = ModuleType("network")
        network_stub.WLAN = WLAN
        network_stub.STA_IF = 0
        sys.modules["network"] = network_stub
