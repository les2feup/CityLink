import os
import json
import time
import network
import asyncio

from umqtt.simple import MQTTClient

def __singleton(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            print("[DEBUG] SSA instance created")
            instance = cls(*args, **kwargs)
        return instance
    return getinstance

@__singleton
class SSA(): 
    def __init__(self):
        self.UUID: str
        self.BASE_TOPIC: str
        self.BASE_ACTION_TOPIC: str
        self.REGISTRATION_TOPIC: str

        self.__wlan: network.WLAN | None = None 
        self.__mqtt: MQTTClient | None = None

        self.__action_cb_dict: Dict[str, funtion] = {}
        self.__tasks: List[asyncio.Task] = []

    def __load_config(self) -> dict[str, Any]:
        CONFIG_FILE_PATH = "../config/config.json"
        SECRETS_FILE_PATH = "../config/secrets.json"

        config: Dict[str, Any] = {}

        try:
            config_file = open(CONFIG_FILE_PATH, "r")
            config = config | json.load(config_file)
            config_file.close()
        except OSError as e:
            raise Exception(f"[ERROR] config.json could not be parsed: {e}")

        try:
            secrets_file = open(SECRETS_FILE_PATH, "r")
            config = config | json.load(secrets_file)
            secrets_file.close()
        except OSError as e:
            raise Exception(f"[ERROR] secrets.json could not be parsed: {e}")

        return config

    def __validate_config(self, CONFIG: Dict[str, Any]):
        try:
            # WIFI Config
            CONFIG["wifi"]
            CONFIG["wifi"]["ssid"]
            CONFIG["wifi"]["password"]

            # Broker Config
            CONFIG["broker"]
            CONFIG["broker"]["host"]
            CONFIG["broker"]["port"]

            # Self identification config
            CONFIG["self-id"]
            CONFIG["self-id"]["uuid"]
            CONFIG["self-id"]["model"]
            CONFIG["self-id"]["version"]
            CONFIG["self-id"]["version"]["instance"]
            CONFIG["self-id"]["version"]["model"]
        except Exception as e:
            raise Exception(f"[ERROR] malformed config: Missing \"{e}\" key")

        self.UUID = CONFIG["self-id"]["uuid"]
        self.BASE_TOPIC = f"{CONFIG["self-id"]['model']}/{self.UUID}"
        self.BASE_ACTION_TOPIC = f"{self.BASE_TOPIC}/actions"
        self.REGISTRATION_TOPIC = f"registration/{self.UUID}"

    def __handle_config_change(self, msg: str):
        raise Exception(f"[TODO] ssa.__handle_config_change not implemented: {msg}")

    def __wlan_connect(self, SSID: str, PASSWORD: str):
        #TODO: Retries with timeout
        #TODO: Check if already connected
        #TODO: Check if given SSID exits

        self.__wlan = network.WLAN(network.STA_IF)
        self.__wlan.active(True)
        self.__wlan.connect(SSID, PASSWORD)

        print("[INFO] connecting to WiFi...", end="")
        while not self.__wlan.isconnected():
            time.sleep(1)
            print(".", end="")
        print("\n[INFO] connected! IP Address:", self.__wlan.ifconfig()[0])

    def __mqtt_connect(self,
                       client_id: str,
                       broker: str,
                       port: int,
                       last_will: str | None = None):
        #TODO: Improve error handling
        #TODO: Check if already connected
        #TODO: Retries with timeout
        #TODO: Add security

        self.__mqtt = MQTTClient(client_id, broker, port)

        if last_will is not None and len(last_will) > 0:
            topic = f"{self.BASE_TOPIC}/last_will",
            self.__mqtt.set_last_will(topic, last_will, qos=1)

        print("Attempting to connect to MQTT broker")
        self.__mqtt.connect()
        print("Connected to MQTT broker")

    def __mqtt_get_subtopic(self, topic: str) -> str:
        topic = topic.decode("utf-8")
        return topic.split("/")[-1]

    def __mqtt_sub_callback(self, topic: bytes, msg: bytes):
        print(f"[DEBUG] Received message from {topic}: {msg}")

        if topic is None:
            print("[WARNING] Received message from invalid topic. Ignoring.")
            return

        action = self.__mqtt_get_subtopic(topic)
        if action not in self.__action_cb_dict.keys():
            print(f"[WARNING] Received message for unregistered action: {action}. Ignoring.")
            return

        print(f"[DEBUG] Executing action callback for {action}")

        try:
            self.__action_cb_dict[action](msg)
        except Exception as e:
            print(f"[WARNING] action callback {self.__action_cb_dict[action].__name__} failed to execute: {e}")

    def connect(self, last_will: str | None = None):
        CONFIG = self.__load_config()
        self.__validate_config(CONFIG)

        try:
            WIFI_SSID = CONFIG["wifi"]["ssid"]
            WIFI_PASSWORD = CONFIG["wifi"]["password"]
            self.__wlan_connect(WIFI_SSID, WIFI_PASSWORD)
        except Exception as e:
            raise Exception(f"[ERROR] wlan connection failed: {e}")

        try:
            MQTT_HOST = CONFIG['broker']['host']
            MQTT_PORT = CONFIG['broker']['port']
            self.__mqtt_connect(self.UUID, MQTT_HOST, MQTT_PORT)
        except Exception as e:
            raise Exception(f"[ERROR] MQTT broker connection failed: {e}")

        #TODO: Improve registration process to be more robust
        self.__mqtt.publish(self.REGISTRATION_TOPIC,
                          json.dumps(CONFIG["self-id"]), retain=True, qos=1)

    def publish(self, subtopic:str, msg:str, qos: int = 0):
        print(f"Publishing {msg} to {subtopic}")
        self.__mqtt.publish(f"{self.BASE_TOPIC}/{subtopic}", msg, qos=qos)

    def register_handler(self, task: function):
        self.__tasks.append(asyncio.create_task(task()))

    def action_callback(self, action:str, callback_func: funtion, qos: int = 0):
        self.__action_cb_dict[action] = callback_func

    #TODO: improve main loop periodicity by taking into account the time taken by check_msg callback
    async def main_loop(self):
        self.__mqtt.set_callback(self.__mqtt_sub_callback)
        self.__mqtt.subscribe(f"{self.BASE_ACTION_TOPIC}/#", qos=1)

        self.action_callback("config", self.__handle_config_change)

        while True:
            self.__mqtt.check_msg()
            #TODO: Add a way to stop the loop
            #TODO: Allow for configuration of the loop period
            await asyncio.sleep_ms(200)

__all__ = ["connect", "publish", "set_action_handler"]
