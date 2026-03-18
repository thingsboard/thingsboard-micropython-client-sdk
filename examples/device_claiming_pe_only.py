"""
MicroPython example: connect to Wi-Fi and claim a device in ThingsBoard
using the ThingsBoard MicroPython Client SDK.
"""

import network
import time

from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient

# --- Wi-Fi settings ---
WIFI_SSID = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# --- ThingsBoard connection settings ---
THINGSBOARD_HOST = "thingsboard.cloud"
# 1883 = MQTT without TLS, 8883 = MQTT with TLS
THINGSBOARD_PORT = 1883

# Device access token (from ThingsBoard device details)
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# Customer enters this key in the Device Claiming widget
SECRET_KEY = "DEVICE_SECRET_KEY"

# Claiming duration in milliseconds (how long the claim request is valid)
DURATION_MS = 30000

# --- Connect to Wi-Fi ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    print('Connecting to network...')
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        pass

print("Wi-Fi connected! Network config:", wlan.ifconfig())

client = None

try:
    # Create ThingsBoard MQTT client
    client = TBDeviceMqttClient(
        host=THINGSBOARD_HOST,
        port=THINGSBOARD_PORT,
        access_token=ACCESS_TOKEN,
    )

    # Connect to ThingsBoard
    print("Connecting to ThingsBoard...")
    client.connect()
    print("Connected to ThingsBoard")

    # Send device claiming request
    print("Sending claiming request...")
    client.claim_device(secret_key=SECRET_KEY, duration_ms=DURATION_MS)
    print("Claiming request was sent")

    # Keep the script alive for the claiming window
    # (so the device stays online while the claim is performed)
    time.sleep_ms(DURATION_MS)

except Exception as e:
    print("Failed to execute device claiming:", e)

finally:
    # Disconnect cleanly
    if client is not None:
        try:
            client.disconnect()
        except Exception as e:
            print("Disconnect failed:", e)
    print("Connection closed")
