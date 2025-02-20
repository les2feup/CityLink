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
            print("init instance")
            instance = cls(*args, **kwargs)
        return instance
    return getinstance

@__singleton
class SSA(): 
    def __init__(self):
        self.UUID: str
        self.BASE_TOPIC: str
        self.REGISTRATION_TOPIC: str

        self.wlan: network.WLAN | None = None 
        self.mqtt: MQTTClient | None = None

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
        self.REGISTRATION_TOPIC = f"registration/{self.UUID}"

    def __wlan_connect(self, SSID: str, PASSWORD: str):
        #TODO: Retries with timeout
        #TODO: Check if already connected
        #TODO: Check if given SSID exits

        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(SSID, PASSWORD)

        print("[INFO] connecting to WiFi...", end="")
        while not self.wlan.isconnected():
            time.sleep(1)
            print(".", end="")
        print("\n[INFO] connected! IP Address:", self.wlan.ifconfig()[0])

    def __mqtt_connect(self,
                       client_id: str,
                       broker: str,
                       port: int,
                       last_will: str | None = None):
        #TODO: Improve error handling
        #TODO: Check if already connected
        #TODO: Retries with timeout
        #TODO: Add security

        self.mqtt = MQTTClient(client_id, broker, port)

        if last_will is not None and len(last_will) > 0:
            topic = f"{self.BASE_TOPIC}/last_will",
            self.mqtt.set_last_will(topic, last_will, qos=1)

        print("Attempting to connect to MQTT broker")
        self.mqtt.connect()
        print("Connected to MQTT broker")

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
        self.mqtt.publish(self.REGISTRATION_TOPIC,
                          json.dumps(CONFIG["self-id"]), retain=True, qos=1)

    def disconnect(self):
        self.mqtt.disconnect()

    def publish(self, subtopic:str, msg:str, qos: int = 0):
        print(f"Publishing {msg} to {subtopic}")
        self.mqtt.publish(f"{self.BASE_TOPIC}/{subtopic}", msg, qos=qos)


__all__ = ["connect", "disconnect", "publish"]
