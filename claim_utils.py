#      Copyright 2025. ThingsBoard
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
