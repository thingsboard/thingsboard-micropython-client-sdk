"""
This sketch demonstrates connecting and device claiming using ThingsBoard SDK,
"""

import network
from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient


WIFI_SSID = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# Thingsboard we want to establish a connection to
THINGSBOARD_HOST = "thingsboard.cloud"
# MQTT port used to communicate with the server, 1883 is the default unencrypted MQTT port,
# whereas 8883 would be the default encrypted SSL MQTT port
THINGSBOARD_PORT = 1883
# See https://thingsboard.io/docs/getting-started-guides/helloworld/
# to understand how to obtain an access token
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# Customer should write this key in device claiming widget
SECRET_KEY = "DEVICE_SECRET_KEY"
DURATION = 30000

# Enabling WLAN interface
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Establishing connection to the Wi-Fi
if not wlan.isconnected():
    print('Connecting to network...')
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        pass

print('Connected! Network config:', wlan.ifconfig())

# Initialising client to communicate with ThingsBoard
client = TBDeviceMqttClient(host=THINGSBOARD_HOST, port=THINGSBOARD_PORT, access_token=ACCESS_TOKEN)
# Connect to ThingsBoard
client.connect()
# Claiming device using secret key and duration for claiming in milliseconds
client.claim_device(secret_key=SECRET_KEY, duration_ms=DURATION)

client.disconnect()
