from gc import collect

from sdk_core.provision_client import ProvisionClientBase
from .umqtt import MQTTClient


class ProvisionClient(ProvisionClientBase):
    def __init__(self, host, port, provision_request):
        super().__init__(host, port, provision_request)

        mqtt_client = MQTTClient(self._client_id, self._host, self._port, keepalive=10)
        mqtt_client.set_callback(self.on_message_callback)
        self.set_client(mqtt_client)

    def provision(self):
        try:
            super().provision()

            self._client.wait_msg()
        finally:
            if self._client:
                self._client.disconnect()

            collect()
