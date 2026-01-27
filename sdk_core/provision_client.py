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

from ujson import dumps, loads
from gc import collect


class ProvisionClient:
    PROVISION_REQUEST_TOPIC = b"/provision/request"
    PROVISION_RESPONSE_TOPIC = b"/provision/response"

    def __init__(self, mqtt_client, provision_request):
        self._mqtt_client = mqtt_client
        self._client_id = b"provision"
        self._provision_request = provision_request
        self._credentials = None

    def _on_message(self, topic, msg):
        try:
            response = loads(msg)
            if response.get("status") == "SUCCESS":
                self._credentials = response
            else:
                print(f"Provisioning failed: {response.get('errorMsg', 'Unknown error')}")
        except MemoryError:
            print("MemoryError during message processing!")

    def provision(self):
        mqtt_client = None
        try:
            collect()

            self._mqtt_client.set_callback(self._on_message)
            self._mqtt_client.connect(clean_session=True)
            self._mqtt_client.subscribe(self.PROVISION_RESPONSE_TOPIC)
            collect()

            provision_request_str = dumps(self._provision_request, separators=(',', ':'))
            self._mqtt_client.publish(self.PROVISION_REQUEST_TOPIC, provision_request_str)
            del provision_request_str
            collect()

            # self._mqtt_client.wait_msg()
        finally:
            if mqtt_client:
                self._mqtt_client.disconnect()
            collect()

    @property
    def credentials(self):
        return self._credentials
