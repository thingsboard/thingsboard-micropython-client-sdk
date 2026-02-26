"""
This sketch demonstrates connecting and retrieving attributes using ThingsBoard SDK
"""

import time

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

# Flag to indicate that we received the attributes from the server, so we can exit the loop and disconnect
IS_ATTR_RECEIVED = False

def on_attributes_change(result, exception=None):
    # This is a callback function that will be called when we receive the response from the server

    global IS_ATTR_RECEIVED

    if exception is not None:
        print("Exception: " + str(exception))
    else:
        print(result)

    IS_ATTR_RECEIVED = True

# Initialising client to communicate with ThingsBoard
client = TBDeviceMqttClient(host=THINGSBOARD_HOST, port=THINGSBOARD_PORT, access_token=ACCESS_TOKEN)
# Connect to ThingsBoard
client.connect()
# Sending data to retrieve it later
client.send_attributes({"atr1": "value1", "atr2": "value2"})
# Requesting attributes
client.request_attributes(["atr1", "atr2"], callback=on_attributes_change)

# Wait until we receive the attributes from the server
while not IS_ATTR_RECEIVED:
    time.sleep(1)

# Disconnect from ThingsBoard
client.disconnect()
