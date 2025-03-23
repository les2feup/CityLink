import sys
from types import ModuleType


class WLAN:
    def __init__(self, *args, **kwargs):
        """
        Initialize a WLAN instance.

        Accepts variable positional and keyword arguments but does not perform any operations.
        """
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
        """
        Placeholder for network interface configuration.

        This stub method accepts arbitrary arguments and keyword arguments without performing any action.
        """
        pass


def load_stub():
    """
    Registers a network module stub if not already loaded.

    If the "network" module is absent from sys.modules, this function creates a stub module,
    assigns the WLAN class and a STA_IF constant (set to 0) to it, and adds it to sys.modules.
    """
    if "network" not in sys.modules:
        network_stub = ModuleType("network")
        network_stub.WLAN = WLAN
        network_stub.STA_IF = 0
        sys.modules["network"] = network_stub
