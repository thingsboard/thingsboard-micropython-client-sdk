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

from gc import collect

from sdk_core.device_mqtt import TBDeviceMqttClientBase
from sdk_core.provision_client import ProvisionClient
from .umqtt import MQTTClient, MQTTException


class TBDeviceMqttClient(TBDeviceMqttClientBase):
    def __init__(self, host, port=1883, access_token=None, quality_of_service=None,
                 client_id=None, chunk_size=0):
        client = MQTTClient(
            self._client_id, self._host, self._port, self._access_token, 'pswd', keepalive=120
        )
        super().__init__(client, host, port, access_token, quality_of_service, client_id, chunk_size)

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


# class ProvisionManager:
#     def __init__(self, host, port=1883):
#         self.host = host
#         self.port = port
#         self.credentials = None
#
#     def provision_device(self,
#                          provision_device_key,
#                          provision_device_secret,
#                          device_name=None,
#                          access_token=None,
#                          client_id=None,
#                          username=None,
#                          password=None,
#                          hash=None,
#                          gateway=None):
#
#         collect()
#         try:
#             provision_request = {
#                 "provisionDeviceKey": provision_device_key,
#                 "provisionDeviceSecret": provision_device_secret
#             }
#
#             if access_token:
#                 provision_request["token"] = access_token
#                 provision_request["credentialsType"] = "ACCESS_TOKEN"
#             elif username or password or client_id:
#                 provision_request["username"] = username
#                 provision_request["password"] = password
#                 provision_request["clientId"] = client_id
#                 provision_request["credentialsType"] = "MQTT_BASIC"
#             elif hash:
#                 provision_request["hash"] = hash
#                 provision_request["credentialsType"] = "X509_CERTIFICATE"
#
#             if device_name:
#                 provision_request["deviceName"] = device_name
#
#             if gateway:
#                 provision_request["gateway"] = gateway
#
#             provision_client = ProvisionClient(self.host, self.port, provision_request)
#
#             provision_client.provision()
#
#             if provision_client.credentials:
#                 print("Provisioning successful. Credentials obtained.")
#                 self.credentials = provision_client.credentials
#                 return self.credentials
#             else:
#                 print("Provisioning failed. No credentials obtained.")
#         finally:
#             collect()
