"""
This sketch demonstrates sending attributes and telemetry in different formats using ThingsBoard SDK
"""

from time import time

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

# Telemetry messages that we will send
telemetry = {"temperature": 41.9, "humidity": 69, "enabled": False, "currentFirmwareVersion": "v1.2.2"}
telemetry_as_array = [{"temperature": 42.0}, {"humidity": 70}, {"enabled": True}, {"currentFirmwareVersion": "v1.2.3"}]
telemetry_with_ts = {"ts": int(round(time() * 1000)), "values": {"temperature": 42.1, "humidity": 70}}
telemetry_with_ts_as_array = [{"ts": 1451649600000, "values": {"temperature": 42.2, "humidity": 71}},
                              {"ts": 1451649601000, "values": {"temperature": 42.3, "humidity": 72}}]
attributes = {"sensorModel": "DHT-22", "attribute_2": "value"}
# Initialising client to communicate with ThingsBoard
client = TBDeviceMqttClient(host=THINGSBOARD_HOST, port=THINGSBOARD_PORT, access_token=ACCESS_TOKEN)
# Connect to ThingsBoard
client.connect()
# Sending telemetry without checking the delivery status
client.send_attributes(attributes)
client.send_telemetry(telemetry)
client.send_telemetry(telemetry_as_array)
client.send_telemetry(telemetry_with_ts)
client.send_telemetry(telemetry_with_ts_as_array)
# Disconnect from ThingsBoard
client.disconnect()
