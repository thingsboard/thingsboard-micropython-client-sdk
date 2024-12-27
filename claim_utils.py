import ujson as json

def claim_device(mqtt_client, secret_key=None, duration_ms=None, qos=1):
    claim_request = {}
    if secret_key:
        claim_request["secretKey"] = secret_key
    if duration_ms:
        claim_request["durationMs"] = duration_ms

    try:
        payload = json.dumps(claim_request)
        topic = "v1/devices/me/claim"
        print(f"Sending claim request to topic '{topic}' with payload: {payload}")
        mqtt_client.publish(topic, payload, qos=qos)
    except Exception as e:
        print(f"Error sending claim request: {e}")
        raise
