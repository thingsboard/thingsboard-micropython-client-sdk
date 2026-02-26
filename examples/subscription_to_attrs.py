"""
This sketch demonstrates connecting and subscribing to attributes updates using ThingsBoard SDK
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

# This is a callback function that will be called when we receive the response from the server
def on_attributes_change(result, *args):
    print(args)
    print('Received attributes: ', result)


# Initialising client to communicate with ThingsBoard
client = TBDeviceMqttClient(host=THINGSBOARD_HOST, port=THINGSBOARD_PORT, access_token=ACCESS_TOKEN)
# Connect to ThingsBoard
client.connect()

# Subscribe to changes of a specific attribute (e.g. "uploadFrequency") and to all attributes changes
client.subscribe_to_attribute("uploadFrequency", on_attributes_change)
client.subscribe_to_all_attributes(on_attributes_change)

while True:
    # Wait until we receive the attributes from the server
    client.wait_for_msg()
