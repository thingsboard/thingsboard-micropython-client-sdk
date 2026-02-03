"""
This sketch demonstrates connecting to Wi-Fi, connecting to ThingsBoard over MQTT,
and handling server-side RPC requests (blocking loop).
"""

import network
import os
from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient

WIFI_SSID = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# Thingsboard host we want to establish a connection to
THINGSBOARD_HOST = "thingsboard.cloud"
# MQTT port used to communicate with the server, 1883 is the default unencrypted MQTT port,
# whereas 8883 would be the default encrypted SSL MQTT port
THINGSBOARD_PORT = 1883
# See https://thingsboard.io/docs/getting-started-guides/helloworld/
# to understand how to obtain an access token
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
# Supported RPC methods in this example they simulate basic filesystem operations
RPC_METHODS = ("Pwd", "Ls")

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


# This callback will be called when an RPC request is received from ThingsBoard.
def on_server_side_rpc_request(request_id, request_body):
    # request_id: numeric id from the MQTT topic
    # request_body: decoded JSON dict, typically {"method": "...", "params": ...}
    print("[RPC] id:", request_id, "body:", request_body)

    # Validate incoming payload type
    if not isinstance(request_body, dict):
        print("[RPC] bad request format (not a dict)")
        return

    # Extract method name and parameters from the RPC payload
    method = request_body.get("method")
    params = request_body.get("params")

    # Reject unknown methods
    if method not in RPC_METHODS:
        reply = {"error": "Unsupported method", "method": method}
        # Send RPC response back to ThingsBoard (method name depends on your SDK wrapper)
        client.send_rpc_reply(request_id, reply)
        return

    # RPC: "Pwd" - return current working directory on the device filesystem
    if method == "Pwd":
        reply = {"current_directory": os.getcwd()}
        client.send_rpc_reply(request_id, reply)

    # RPC: "Ls" - list files in a directory
    elif method == "Ls":
        try:
            # If params is missing/empty, default to root ("/") or current dir
            if not params:
                params = "/"
            # Here we treat params directly as a path string for simplicity.
            files = os.listdir(params)
            reply = {"path": params, "files": files}
        except Exception as e:
            reply = {"error": str(e)}

        client.send_rpc_reply(request_id, reply)


# Initialising client to communicate with ThingsBoard
client = TBDeviceMqttClient(THINGSBOARD_HOST, port=THINGSBOARD_PORT, access_token=ACCESS_TOKEN)
# Register the server-side RPC callback before the main loop
client.set_server_side_rpc_request_handler(on_server_side_rpc_request)
# Connect to ThingsBoard
client.connect()

# Main loop (blocking)
while True:
    # wait_for_msg() blocks until an MQTT message arrives.
    # This is simplest for an RPC-only demo, but it can block other device logic.
    print("Waiting for RPC requests... blocking")
    client.wait_for_msg()
