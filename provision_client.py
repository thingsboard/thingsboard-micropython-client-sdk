import ujson
from umqtt import MQTTClient
import gc


class ProvisionClient:
    PROVISION_REQUEST_TOPIC = b"/provision/request"
    PROVISION_RESPONSE_TOPIC = b"/provision/response"

    def __init__(self, host, port, provision_request):
        self._host = host
        self._port = port
        self._client_id = b"provision"
        self._provision_request = provision_request
        self._credentials = None

    def _on_message(self, topic, msg):
        try:
            response = ujson.loads(msg)
            if response.get("status") == "SUCCESS":
                self._credentials = response
            else:
                print(f"Provisioning failed: {response.get('errorMsg', 'Unknown error')}")
        except MemoryError:
            print("MemoryError during message processing!")

    def provision(self):
        try:
            gc.collect()

            mqtt_client = MQTTClient(self._client_id, self._host, self._port, keepalive=10)
            mqtt_client.set_callback(self._on_message)
            mqtt_client.connect(clean_session=True)
            mqtt_client.subscribe(self.PROVISION_RESPONSE_TOPIC)
            gc.collect()

            provision_request_str = ujson.dumps(self._provision_request, separators=(',', ':'))
            mqtt_client.publish(self.PROVISION_REQUEST_TOPIC, provision_request_str)
            del provision_request_str
            gc.collect()

            mqtt_client.wait_msg()
        except MemoryError:
            print("Memory error during provisioning!")
        except Exception as e:
            print(f"Provisioning error {e}")
        finally:
            mqtt_client.disconnect()
            gc.collect()

    @property
    def credentials(self):
        return self._credentials
