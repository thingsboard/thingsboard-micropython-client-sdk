from machine import Pin, PWM
import network, time

WIFI_SSID = "YOUR_NETWORK_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    print('Connecting to network...')
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        pass

print("connected:", wlan.isconnected())
print("ifconfig:", wlan.ifconfig())

import mip

# Install ThingsBoard SDK only if it's missing
try:
    from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient
    print("thingsboard-micropython-client-sdk package already installed.")
except ImportError:
    print("Installing thingsboard-micropython-client-sdk package...")
    mip.install('github:thingsboard/thingsboard-micropython-client-sdk')
    from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient

# ThingsBoard connection settings
HOST = "YOUR_HOST"
PORT = "YOUR_PORT"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

# GPIO mapping
SENSOR_PIN = 18
LED_WHITE_PIN = 23

# 16-bit PWM max value for duty_u16()
U16_MAX = 65535

# Fade behavior tuning (time-based)
FULL_PERIOD_MS = 10000
FADE_STEP_SLEEP_MS = 100
FADE_UPDATE_MS = 500

# Loop/telemetry intervals
STAT_PERIOD_MS = 10_000
MAIN_LOOP_SLEEP_MS = 10
RELEASE_POLL_MS = 200

# RPC method name expected from ThingsBoard dashboard
RPC_METHOD_SET_BRIGHTNESS = "setBrightnessPct"

# Initialize input (touch sensor) and PWM output (LED)
sensor = Pin(SENSOR_PIN, Pin.IN)
led_pwm = PWM(Pin(LED_WHITE_PIN), freq=1000)
led_pwm.duty_u16(0)  # start OFF

# Shared state used by touch logic + RPC logic
state = {
    "brightness": 0,
    "direction_up": True,
    "percentage_light": 0,
    "is_touched": False
}

def set_brightness_u16(x):
    # Clamp brightness into valid PWM range, then apply it
    if x < 0:
        x = 0
    if x > U16_MAX:
        x = U16_MAX
    led_pwm.duty_u16(x)

def calculate_value_from_time(passed_ms):
    # Map elapsed time (0..FULL_PERIOD_MS) to PWM value (0..U16_MAX)
    if passed_ms < 0:
        passed_ms = 0
    if passed_ms >= FULL_PERIOD_MS:
        passed_ms = FULL_PERIOD_MS
    return int((passed_ms * U16_MAX) / FULL_PERIOD_MS)

def wait_release(sensor):
    # When we hit min/max, wait until user releases the touch sensor
    while sensor.value() == 1:
        time.sleep_ms(RELEASE_POLL_MS)

def connect_to_broker(client):
    # Connect to ThingsBoard MQTT broker with basic error handling
    try:
        client.connect()
        print("Connected to MQTT broker")
        return True
    except OSError as e:
        print("[TB] connect OSError:", e)
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
    return False

def send_state_telemetry(client, sensor, state):
    # Prepare and send current device state to ThingsBoard
    telemetry = {
        "brightness": state["brightness"],
        "is_touched": bool(sensor.value()),
        "percentage_light": int((state["brightness"] * 100) / U16_MAX),
        "is_growing": state["direction_up"],
    }
    try:
        client.send_telemetry(telemetry)
    except Exception as e:
        print("[TB] send_telemetry failed:", e)
    return telemetry

def parse_rpc_brightness_params(params):
    # Validate and clamp RPC brightness percent (0..100)
    if params is None:
        raise ValueError("Params is None")
    percents = int(params)
    if percents < 0:
        percents = 0
    if percents > 100:
        percents = 100
    return percents

def on_server_side_rpc_request(request_id, request_body):
    # Called automatically when ThingsBoard sends an RPC request
    print("[RPC] id:", request_id, "body:", request_body)

    try:
        method = request_body.get("method")
        params = request_body.get("params")
    except AttributeError:
        print("[RPC] bad request format (not a dict)")
        return

    # Ignore unknown methods (keep callback strict)
    if method != RPC_METHOD_SET_BRIGHTNESS:
        print("Such method is not supported:", method)
        return

    try:
        # Convert percent to PWM duty and apply immediately
        pct = parse_rpc_brightness_params(params)
        brightness = int((pct * U16_MAX) / 100)

        state["brightness"] = brightness
        set_brightness_u16(brightness)

        # Keep fade direction consistent after remote control
        if brightness <= 0:
            state["direction_up"] = True
        elif brightness >= U16_MAX:
            state["direction_up"] = False

        # Defer reply sending to the main loop (safer than publishing inside callback)
        reply = {"brightness": brightness, "percentage_light": pct, "is_growing": state["direction_up"]}
        state["pending_rpc_reply"] = (request_id, reply)

    except ValueError as e:
        print("[RPC] invalid params:", e)
    except Exception as e:
        print("[RPC] handler error:", e)

def safe_check_msg(client):
    # Non-blocking poll for incoming MQTT packets (RPC/attribute updates)
    try:
        client.check_for_msg()
        return True
    except OSError as e:
        print("[TB] check_msg OSError:", e)
        # Try reconnect once if the socket broke
        if not connect_to_broker(client):
            print("[TB] Reconnection failed")
    except Exception as e:
        print(f"Failed to check messages: {e}")
    return False

def send_pending_rpc_reply(client, state):
    # Send RPC reply later from the main loop (avoids heavy work in callback)
    pending = state.get("pending_rpc_reply")
    if pending is not None:
        request_id, reply = pending
        state["pending_rpc_reply"] = None
        try:
            client.send_rpc_reply(request_id, reply)
        except Exception as e:
            print("[RPC] publish failed in main loop:", e)

        # Optionally mirror reply as telemetry for easier dashboard sync
        try:
            client.send_telemetry(reply)
        except Exception as e:
            print("[TB] send_telemetry failed in main loop:", e)

def fade(client, sensor, state, direction_up):
    # Time-based fade while the touch sensor is pressed
    state["direction_up"] = direction_up

    now = time.ticks_ms()
    start_brightness = state["brightness"]

    # Continue fade from current level (not from 0/100)
    if direction_up:
        elapsed_ms = int((start_brightness * FULL_PERIOD_MS) / U16_MAX)
    else:
        elapsed_ms = int(((U16_MAX - start_brightness) * FULL_PERIOD_MS) / U16_MAX)
    start_time = time.ticks_add(now, -elapsed_ms)

    while sensor.value() == 1:
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)
        progress = calculate_value_from_time(elapsed)

        if direction_up:
            # Increase toward max
            inc = int((progress * (U16_MAX - start_brightness)) / U16_MAX)
            state["brightness"] = start_brightness + inc
            if state["brightness"] >= U16_MAX:
                state["brightness"] = U16_MAX
                set_brightness_u16(state["brightness"])
                state["direction_up"] = False
                wait_release(sensor)
                send_state_telemetry(client, sensor, state)
                break
        else:
            # Decrease toward 0
            dec = int((progress * start_brightness) / U16_MAX)
            state["brightness"] = start_brightness - dec
            if state["brightness"] <= 0:
                state["brightness"] = 0
                set_brightness_u16(state["brightness"])
                state["direction_up"] = True
                wait_release(sensor)
                send_state_telemetry(client, sensor, state)
                break

        set_brightness_u16(state["brightness"])
        send_state_telemetry(client, sensor, state)
        time.sleep_ms(FADE_UPDATE_MS)
        time.sleep_ms(FADE_STEP_SLEEP_MS)

def main():
    # Main loop: handle touch events + periodic telemetry + RPC polling
    prev_touch = 0
    client = TBDeviceMqttClient(HOST, PORT, access_token=ACCESS_TOKEN)

    # Register RPC callback before connecting
    client.set_server_side_rpc_request_handler(on_server_side_rpc_request)

    connect_to_broker(client)
    send_state_telemetry(client, sensor, state)
    set_brightness_u16(0)

    last_stat_ms = time.ticks_ms()
    try:
        while True:
            # Touch edge detection (press event)
            touch = sensor.value()
            if touch == 1 and prev_touch == 0:
                if state["direction_up"]:
                    fade(client, sensor, state, direction_up=True)
                else:
                    fade(client, sensor, state, direction_up=False)
                print("Released; holding brightness:", state["brightness"])

            prev_touch = touch

            # Periodic "status" telemetry (even if no touches happen)
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, last_stat_ms) >= STAT_PERIOD_MS:
                last_stat_ms = now_ms
                telemetry = send_state_telemetry(client, sensor, state)
                print("Stat telemetry:", telemetry)

            # Process RPC messages and send pending replies
            safe_check_msg(client)
            send_pending_rpc_reply(client, state)

            time.sleep_ms(MAIN_LOOP_SLEEP_MS)

    finally:
        # Safe shutdown: turn LED off and disconnect
        try:
            set_brightness_u16(0)
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception as e:
            print("Could not disconnect client:", e)

main()
