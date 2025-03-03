from ssa.interfaces import NetworkDriver
from network import WLAN, STA_IF
from time import sleep_ms

class GenericWLANDriver(NetworkDriver):
    """
    Default WLAN driver for the Smart Sensor Actuator framework
    """
    def __init__(self, config):
        """
        Initialize the GenericWLANDriver with network configuration.
        
        This constructor sets up a WLAN interface in station mode, activates it, and attempts
        to connect to the network using the credentials provided in the configuration
        dictionary. The dictionary must include the keys 'ssid' and 'password' corresponding
        to the network’s SSID and password.
        """
        self._wlan = WLAN(STA_IF)
        self._wlan.active(True)
        self._wlan.connect(config["ssid"], config["password"])
    
    def connect(self, retries, base_timeout_ms, **_):
        """
        Attempts to connect to the WLAN using exponential backoff.
        
        This method repeatedly polls the WLAN connection status. It waits for an
        interval that doubles with each retry and returns immediately if the WLAN
        becomes connected. If the WLAN remains disconnected after the specified
        number of retries, an exception is raised.
        
        Args:
            retries: The maximum number of connection attempts.
            base_timeout_ms: The initial wait time in milliseconds.
        
        Raises:
            Exception: If the WLAN fails to connect after all retries.
        """
        for retry in range(retries):
            print(f"[INFO] Attempting WLAN connection (retry {retry + 1}/{retries})")
            if self._wlan.isconnected():
                print(f"[INFO] WLAN connected with IP: {self.get_ip()}")
                return
            sleep_ms(base_timeout_ms * 2**retry)
        raise Exception("[FATAL] Failed to connect to WLAN")
    
    def disconnect(self):
        """
        Disconnects from the WLAN network.
        
        This method calls the disconnect function of the underlying WLAN interface to
        terminate any active WLAN connection.
        """
        self._wlan.disconnect()
    
    def get_ip(self):
        """
        Retrieve the current IP address of the WLAN connection.
        
        If the WLAN interface is connected, returns the primary IP address from its
        configuration; otherwise, returns None.
        """
        if self._wlan.isconnected():
            return self._wlan.ifconfig()[0]
        return None
