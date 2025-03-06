from ssa.interfaces import NetworkDriver
from network import WLAN, STA_IF
from time import sleep_ms


class GenericWLANDriver(NetworkDriver):

    def __init__(self, config):
        self._wlan = WLAN(STA_IF)
        self._wlan.active(True)
        self._wlan.connect(config['ssid'], config['password'])

    def connect(self, retries, base_timeout_ms, **_):
        for retry in range(retries):
            print(
                f'[INFO] Attempting WLAN connection (retry {retry + 1}/{retries})'
                )
            if self._wlan.isconnected():
                print(f'[INFO] WLAN connected with IP: {self.get_ip()}')
                return
            sleep_ms(base_timeout_ms * 2 ** retry)
        raise Exception(
            f'[FATAL] Failed to connect to WLAN after {retries} attempts')

    def disconnect(self):
        self._wlan.disconnect()

    def get_ip(self):
        if self._wlan.isconnected():
            return self._wlan.ifconfig()[0]
        return None
