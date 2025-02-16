"""
Simple MQTT publisher script for Raspberry Pi Pico W to test WiFi and MQTT connectivity.

This script connects to a WiFi network and publishes a message to an MQTT broker.
The message is published to a topic called "pico-w".
"""

import time
import network
import machine
from umqtt.simple import MQTTClient

"""
WIFI_SSID = "Your WiFi SSID"
WIFI_PASSWORD = "Your WiFi password"
"""
from src.secrets.wifi import *

"""
MQTT_BROKER = "Your MQTT broker IP address"
MQTT_PORT = <port_number> # Default: 1883
"""
from src.secrets.mqtt import *

MQTT_TOPIC = "pico-w"
MQTT_CLIENT_ID = "Pico-W-" + str(machine.unique_id().hex())

def main():
    # Connect to WiFi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    print("Connecting to WiFi...", end="")
    while not wlan.isconnected():
        time.sleep(1)
        print(".", end="")
    print("\nConnected! IP Address:", wlan.ifconfig()[0])

    # Initialize MQTT client
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT)

    try:
        client.connect()
        print("Connected to MQTT broker")

        # Publish a test message
        message = "Hello from Raspberry Pi Pico W!"
        client.publish(MQTT_TOPIC, message)
        print(f"Published message: {message} to topic: {MQTT_TOPIC}")

        while True:
            message = "Hello from Raspberry Pi Pico W! Time: " + str(time.time())
            client.publish(MQTT_TOPIC, message)
            print(f"Published message: {message} to topic: {MQTT_TOPIC}")
            time.sleep(5)

        client.disconnect()
        print("Disconnected from MQTT broker")

    except Exception as e:
        print("Failed to connect or publish:", e)

if __name__ == "__main__":
    main()
