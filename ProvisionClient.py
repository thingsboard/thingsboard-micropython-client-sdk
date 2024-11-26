import ujson
from umqtt import MQTTClient

class ProvisionClient:
    PROVISION_REQUEST_TOPIC = "/provision/request"
    PROVISION_RESPONSE_TOPIC = "/provision/response"

    def __init__(self, host, port, provision_request):
        self._host = host
        self._port = port
        self._client_id = "provision"
        self._provision_request = provision_request
        self._credentials = None

    def _on_message(self, topic, msg):
        response = ujson.loads(msg)
        if response.get("status") == "SUCCESS":
            self._credentials = response
        else:
            error_msg = response.get("errorMsg", "Unknown error")
            print(f"Provisioning error: {error_msg}")

    def provision(self):
        try:
            mqtt_client = MQTTClient(self._client_id, self._host, self._port)
            mqtt_client.set_callback(self._on_message)
            mqtt_client.connect()
            mqtt_client.subscribe(self.PROVISION_RESPONSE_TOPIC)
            mqtt_client.publish(self.PROVISION_REQUEST_TOPIC, ujson.dumps(self._provision_request))

            while self._credentials is None:
                mqtt_client.wait_msg()
        except Exception as e:
            print(f"Provisioning error: {e}")
        finally:
            mqtt_client.disconnect()

    @property
    def credentials(self):
        return self._credentials
