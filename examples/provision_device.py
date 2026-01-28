"""
This sketch demonstrates connecting and provisioning a device using ThingsBoard SDK
"""

import network

from sdk_core.device_mqtt import TBDeviceMqttClientBase
from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient

WIFI_SSID = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# Thingsboard we want to establish a connection to
THINGSBOARD_HOST = "thingsboard.cloud"
# MQTT port used to communicate with the server, 1883 is the default unencrypted MQTT port,
# whereas 8883 would be the default encrypted SSL MQTT port
THINGSBOARD_PORT = 1883
# See
# to understand how to obtain provision device key and device secret
PROVISION_DEVICE_KEY = "YOUR_PROVISION_DEVICE_KEY"
PROVISION_DEVICE_SECRET = "YOUR_PROVISION_DEVICE_SECRET"
# Provisioned device name
DEVICE_NAME = "MyDevice"

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

# Form provision request using provision credentials
provision_request = TBDeviceMqttClientBase.get_provision_request(provision_device_key=PROVISION_DEVICE_KEY,
                                                                 provision_device_secret=PROVISION_DEVICE_SECRET,
                                                                 device_name=DEVICE_NAME)
# Send provision device request
provisioned_credentials = TBDeviceMqttClient.provision(THINGSBOARD_HOST, THINGSBOARD_PORT, provision_request)
print(provisioned_credentials)

if not provisioned_credentials:
    print("Provisioning failed!")
    raise SystemExit("Exiting: Provisioning unsuccessful.")

# Get provisioned credentials
access_token = provisioned_credentials.get("credentialsValue")
if not access_token:
    print("No access token found in credentials!")
    raise SystemExit("Exiting: Access token missing.")

# Telemetry message that we will send
telemetry = {"temperature": 41.9, "enabled": False, "currentFirmwareVersion": "v1.2.2"}
# Initialising client with provisioned credentials to communicate with ThingsBoard
client = TBDeviceMqttClient(host=THINGSBOARD_HOST, port=THINGSBOARD_PORT, access_token=access_token)
# Connect to ThingsBoard
client.connect()
# Sending telemetry without checking the delivery status
client.send_telemetry(telemetry)
# Disconnect from ThingsBoard
client.disconnect()
