import time
import json
import network
import random

from umqtt.simple import MQTTClient

def import_config() -> Dict[str, Any]:
    config = {}
    with open('../config/config.json', 'r') as config_file:
        config = config | json.load(config_file)
    with open('../config/secrets.json', 'r') as secrets_file:
        config = config | json.load(secrets_file)
    return config

def wlan_connect(ssid: str, password: str) -> None:
    #TODO: Error handling
    #TODO: Check if already connected
    #TODO: Retries with timeout
    #TODO: Check if SSID is available

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print("Connecting to WiFi...", end="")
    while not wlan.isconnected():
        time.sleep(1)
        print(".", end="")
    print("\nConnected! IP Address:", wlan.ifconfig()[0])

def mqtt_connect(client_id: str, broker: str, port: int) -> MQTTClient | None:
    #TODO: Improve error handling
    #TODO: Check if already connected
    #TODO: Retries with timeout

    try:
        client = MQTTClient(client_id, broker, port)
        client.connect()
        print("Connected to MQTT broker")
        return client
    except Exception as e:
        print("Failed to connect to MQTT broker:", e)
        return None

def main():
    CONFIG = import_config()

    WIFI_SSID = CONFIG['wifi']['ssid']
    WIFI_PASSWORD = CONFIG['wifi']['password']
    wlan_connect(WIFI_SSID, WIFI_PASSWORD)

    MQTT_HOST = CONFIG['broker']['host']
    MQTT_PORT = CONFIG['broker']['port']
    SELF_ID = CONFIG['self-id']
    UUID = SELF_ID['uuid']
    client = mqtt_connect(UUID, MQTT_HOST, MQTT_PORT)
    if not client:
        return

    #send message to registration topic
    client.publish(f"register/{UUID}", json.dumps(SELF_ID), retain=True, qos=1)

    # generate values on value property topic
    BASE_TOPIC = f"{SELF_ID['model']}/{UUID}"
    while True:
        client.publish(f"{BASE_TOPIC}/value", f"{random.randint(0, 100)}")
        time.sleep(5)


if __name__ == "__main__":
    main()
