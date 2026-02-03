#      Copyright 2026. ThingsBoard
#  #
#      Licensed under the Apache License, Version 2.0 (the "License");
#      you may not use this file except in compliance with the License.
#      You may obtain a copy of the License at
#  #
#          http://www.apache.org/licenses/LICENSE-2.0
#  #
#      Unless required by applicable law or agreed to in writing, software
#      distributed under the License is distributed on an "AS IS" BASIS,
#      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#      See the License for the specific language governing permissions and
#      limitations under the License.
#

from sdk_core.device_mqtt import TBDeviceMqttClientBase
from .provision_client import ProvisionClient
from .umqtt import MQTTClient, MQTTException


class TBDeviceMqttClient(TBDeviceMqttClientBase):
    def __init__(self, host, port=1883, access_token=None, quality_of_service=None,
                 client_id=None, chunk_size=0):
        super().__init__(host, port, access_token, quality_of_service, client_id, chunk_size)
        client = MQTTClient(
            self._client_id, self._host, self._port, self._access_token, 'pswd', keepalive=120
        )
        self.set_client(client)

    def connect(self, timeout=5):
        try:
            response = self._client.connect(timeout=timeout)
            self._client.set_callback(self.all_subscribed_topics_callback)

            self.__subscribe_all_required_topics()

            self.connected = True
            return response
        except MQTTException as e:
            self.connected = False
            print(f"MQTT connection error: {e}")
        except Exception as e:
            self.connected = False
            print(f"Unexpected connection error: {e}")

    def request_attributes(self, client_keys=None, shared_keys=None, callback=None):
        super().request_attributes(client_keys=client_keys, shared_keys=shared_keys, callback=callback)
        self._client.wait_msg()

    def send_rpc_call(self, method, params, callback):
        super().send_rpc_call(method=method, params=params, callback=callback)
        self._client.wait_msg()

    def wait_for_msg(self):
        self._client.wait_msg()

    def check_for_msg(self):
        self._client.check_msg()

    @staticmethod
    def provision(host, port, provision_request):
        provision_client = ProvisionClient(host=host, port=port, provision_request=provision_request)
        provision_client.provision()

        if provision_client.credentials:
            print("Provisioning successful. Credentials obtained.")
            return provision_client.credentials
        else:
            print("Provisioning failed. No credentials obtained.")
            return None
