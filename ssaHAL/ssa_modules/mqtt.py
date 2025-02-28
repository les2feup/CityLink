from umqtt.simple import MQTTClient as UMQTTClient

class MQTTClient():
    """MQTT Client for the Smart Sensor Actuator framework.
    Based on the umqtt.simple library
    Implements the SSA MessagingClient interface.
    @param id: The ID of the client.
    @param config: Configuration dictionary.
    """
    def __init__(self, id, config):
        keepalive = 0 if config.get("keepalive") is None \
                else config.get("keepalive")
        port = 0 if config.get("port") is None \
                else config.get("port")

        server = config.get("server")
        if server is None:
            raise Exception("Server address not found in configuration")

        self._client = UMQTTClient(id,
                                   server,
                                   port,
                                   config.get("user"),
                                   config.get("password"),
                                   keepalive,
                                   config.get("ssl"))
        
        self._clean_session = True if config.get("clean_session") is None \
                else config.get("clean_session")
        self._lw_topic = config.get("lw_topic")
        self._lw_msg = config.get("lw_msg")

        if self._lw_topic is not None:
            self._client.set_last_will(self._lw_topic, self._lw_msg)
        elif self._lw_msg is not None:
            default_topic = f"last_will/{id}"
            self._client.set_last_will(default_topic, self._lw_msg)

        self._connected = False

    def connect(self, retries, base_timeout, subscription=None):
        """Connect to the MQTT broker.
        @param retries: Number of retries to attempt.
        @param base_timeout: Base timeout (in seconds)
        """
        if self._connected:
            return

        if subscription is not None:
            self._client.subscribe(subscription, qos=1)
            

        error = None
        for retry in range(retries):
            try:
                self._client.connect(self._clean_session,
                                     base_timeout * 2**retry)
                self._connected = True
                return
            except Exception as e:
                error = e

        if not self._connected:
            raise Exception(f"Failed to connect to MQTT broker: {error}")

    def is_connected(self):
        """Check if the client is connected.
        @return True if connected, False otherwise.
        """
        return self._connected

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self._client.disconnect()
        self._connected = False

    def sendto(self, uri, message, qos=0, retain=False):
        """Send a message to the message broker, using the pre-configured
        QoS and Retain settings.
        @param uri: The URI to send the message to.
        @param message: The message to send.
        """
        self._client.publish(uri, message, qos, retain)

    def set_callback(self, callback):
        """Set the callback function to handle incoming messages.
        @param callback: The callback function to set.
        """
        self._client.set_callback(callback)

    def check_message(self):
        """Check for incoming message
        and handle it using the callback function.
        Does not block.
        """
        self._client.check_msg()

    def wait_message(self):
        """Block until a message is received 
        and handle it using the callback function.
        """
        self._client.wait_msg()
