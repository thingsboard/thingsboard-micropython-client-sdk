"""
MicroPython example for connecting to Wi-Fi and claiming a device
using the ThingsBoard SDK.
"""

import network
import time

from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient


WIFI_SSID = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# ThingsBoard server we want to connect to
THINGSBOARD_HOST = "thingsboard.cloud"

# MQTT port used to communicate with the server:
# 1883 - default unencrypted MQTT port
# 8883 - default encrypted SSL MQTT port
THINGSBOARD_PORT = 1883

# See https://thingsboard.io/docs/getting-started-guides/helloworld/
# to understand how to obtain an access token
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# Customer should enter this key in the device claiming widget
SECRET_KEY = "123"

# Claiming duration in milliseconds
DURATION = 30000


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        while not wlan.isconnected():
            time.sleep_ms(300)

    print("Connected to Wi-Fi:", wlan.ifconfig())
    return wlan


def main():
    client = None

    try:
        connect_wifi()

        # Initialize client to communicate with ThingsBoard
        client = TBDeviceMqttClient(
            host=THINGSBOARD_HOST,
            port=THINGSBOARD_PORT,
            access_token=ACCESS_TOKEN
        )

        # Connect to ThingsBoard
        client.connect()
        print("Connected to ThingsBoard")

        # Send claiming request
        client.claim_device(secret_key=SECRET_KEY, duration_ms=DURATION)
        print("Claiming request was sent")

        # Keep connection alive during the claiming period
        time.sleep_ms(DURATION)

    except Exception as e:
        print("Failed to execute device claiming:", e)

    finally:
        if client is not None:
            client.disconnect()
        print("Connection closed")


if __name__ == "__main__":
    main()
