from ssa.interfaces import NetworkDriver
from network import WLAN, STA_IF
from time import sleep

class GenericWLANDriver(NetworkDriver):
    """
    Default WLAN driver for the Smart Sensor Actuator framework
    """
    def __init__(self, config):
        self._wlan = WLAN(STA_IF)
        self._wlan.active(True)
        self._wlan.connect(config["ssid"], config["password"])
    
    def connect(self, retries, base_timeout):
        for retry in range(retries):
            if self._wlan.isconnected():
                return
            sleep(base_timeout * 2**retry)
        raise Exception("Failed to connect to WLAN")
    
    def disconnect(self):
        self._wlan.disconnect()
    
    def get_ip(self):
        if self._wlan.isconnected():
            return self._wlan.ifconfig()[0]
        return None
