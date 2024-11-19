import network
import time
import ubinascii
import ujson
from umqtt import MQTTClient


WIFI_SSID = 'ThingsBoard_TN'
WIFI_PASS = '4Friends123!'

# Конфигурация ThingsBoard
THINGSBOARD_HOST = 'demo.thingsboard.io'
ACCESS_KEY = 'qzdd2xhn8us63fdz0s67'
ACCESS_SECRET = 'z320ow0r9kydv20o1bor'
DEVICE_NAME = 'ESP8266_D1evi2ce'
ACCESS_TOKEN = ''

# Топики для ThingsBoard
PROVISION_REQUEST_TOPIC = "/provision/request"
PROVISION_RESPONSE_TOPIC = "/provision/response"


def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        print("Connecting to WiFi...")
        time.sleep(1)

    if wlan.isconnected():
        print(f"Connected to WiFi: {ssid}, IP: {wlan.ifconfig()[0]}")
    else:
        print("Failed to connect to WiFi")
        return False
    return True


def mqtt_callback(topic, msg):
    global ACCESS_TOKEN
    print(f"Topic: {topic}, Message: {msg}")
    response = ujson.loads(msg)
    if 'credentialsValue' in response:
        ACCESS_TOKEN = response['credentialsValue']
        print("Access Token obtained: ", ACCESS_TOKEN)
        send_telemetry(ACCESS_TOKEN)


def send_telemetry(access_token):
    client = MQTTClient(ubinascii.hexlify(network.WLAN().config('mac')).decode(), THINGSBOARD_HOST, 1883,
                        user=access_token, password="")
    try:
        client.connect()
        print("Connected to MQTT Broker with Access Token")
        telemetry_topic = "v1/devices/me/telemetry"
        telemetry_data = ujson.dumps({"temperature": 25})
        client.publish(telemetry_topic, telemetry_data)
        print(f"Telemetry data sent: {telemetry_data}")
    except Exception as e:
        print(f"Failed to send telemetry: {e}")
    finally:
        client.disconnect()


def main():
    if not connect_wifi(WIFI_SSID, WIFI_PASS):
        return

    provision_msg = ujson.dumps({
        "deviceName": DEVICE_NAME,
        "provisionDeviceKey": ACCESS_KEY,
        "provisionDeviceSecret": ACCESS_SECRET,
    })

    client_id = ubinascii.hexlify(network.WLAN().config('mac')).decode()
    client = MQTTClient("provision", THINGSBOARD_HOST, 1883)

    client.set_callback(mqtt_callback)

    try:
        client.connect()
        print("Connected to MQTT Broker")
        client.subscribe(PROVISION_RESPONSE_TOPIC, 1)
        print("Subscribed to ", PROVISION_RESPONSE_TOPIC)
        print("Sending provision request...")
        client.publish(PROVISION_REQUEST_TOPIC, provision_msg)
    except Exception as e:
        print(f"Failed to connect or send provision request: {e}")
        return

    try:
        while True:
            client.wait_msg()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()


main()
