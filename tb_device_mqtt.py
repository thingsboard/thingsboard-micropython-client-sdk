#      Copyright 2023. ThingsBoard
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

import time
from math import ceil

from sdk_utils import verify_checksum
from umqtt import MQTTClient, MQTTException
import ujson
import ubinascii
import machine


FW_TITLE_ATTR = "fw_title"
FW_VERSION_ATTR = "fw_version"
FW_CHECKSUM_ATTR = "fw_checksum"
FW_CHECKSUM_ALG_ATTR = "fw_checksum_algorithm"
FW_SIZE_ATTR = "fw_size"
FW_STATE_ATTR = "fw_state"

REQUIRED_SHARED_KEYS = "{0},{1},{2},{3},{4}".format(FW_CHECKSUM_ATTR, FW_CHECKSUM_ALG_ATTR, FW_SIZE_ATTR, FW_TITLE_ATTR,
                                                    FW_VERSION_ATTR)

RPC_REQUEST_TOPIC = 'v1/devices/me/rpc/request/'
RPC_RESPONSE_TOPIC = 'v1/devices/me/rpc/response/'
ATTRIBUTES_TOPIC = 'v1/devices/me/attributes'
ATTRIBUTE_REQUEST_TOPIC = 'v1/devices/me/attributes/request/'
ATTRIBUTE_TOPIC_RESPONSE = 'v1/devices/me/attributes/response/'


class TBDeviceMqttClient:
    def __init__(self, host, port=1883, access_token=None, quality_of_service=None, client_id=None, chunk_size=0):
        self._host = host
        self._port = port
        self.quality_of_service = quality_of_service if quality_of_service is not None else 1
        self.current_firmware_info = {
            "current_" + FW_TITLE_ATTR: "Initial",
            "current_" + FW_VERSION_ATTR: "v0"
        }
        self._attr_request_dict = {}
        self.__device_client_rpc_dict = {}
        self.__device_sub_dict = {}
        self.__device_on_server_side_rpc_response = None
        self.__attr_request_number = 0
        self.__device_client_rpc_number = 0
        self.__device_max_sub_id = 0
        self.__firmware_request_id = 0
        self.__request_id = 0
        self.__chunk_size = chunk_size
        self.connected = False

        if not access_token:
            print("token is not set, connection without tls wont be established")
        self._access_token = access_token

        if not client_id:
            client_id = ubinascii.hexlify(machine.unique_id())
        self._client_id = client_id
        self._client = MQTTClient(self._client_id, self._host, self._port, self._access_token, 'pswd', keepalive=120)

    def connect(self):
        try:
            response = self._client.connect()
            self._client.set_callback(self._callback)
            self._client.subscribe(ATTRIBUTES_TOPIC, qos=self.quality_of_service)
            self._client.subscribe(ATTRIBUTES_TOPIC + "/response/+", qos=self.quality_of_service)
            self._client.subscribe(RPC_REQUEST_TOPIC + '+', qos=self.quality_of_service)
            self._client.subscribe(RPC_RESPONSE_TOPIC + '+', qos=self.quality_of_service)

            self.connected = True

            return response
        except MQTTException as e:
            self.connected = False
            print(e)

    def disconnect(self):
        self._client.disconnect()
        self.connected = False

    def _callback(self, topic, msg):
        topic = topic.decode('utf-8')
        print('callback', topic, msg)

        update_response_pattern = "v2/fw/response/" + str(self.__firmware_request_id) + "/chunk/"

        if topic.startswith(update_response_pattern):
            firmware_data = msg

            self.firmware_data = self.firmware_data + firmware_data
            self.__current_chunk = self.__current_chunk + 1

            print('Getting chunk with number: %s. Chunk size is : %r byte(s).' % (
                self.__current_chunk, self.__chunk_size))

            if len(self.firmware_data) == self.__target_firmware_length:
                self.__process_firmware()
            else:
                self.__get_firmware()
        else:
            self._on_decode_message(topic, msg)

    def _on_decode_message(self, topic, msg):
        if topic.startswith(RPC_REQUEST_TOPIC):
            self._handle_rpc_request(topic, msg)
        elif topic.startswith(RPC_RESPONSE_TOPIC):
            self._handle_rpc_response(topic, msg)
        elif topic == ATTRIBUTES_TOPIC:
            self._handle_attributes(msg)
        elif topic.startswith(ATTRIBUTE_TOPIC_RESPONSE):
            self._handle_attribute_response(topic, msg)

        if topic.startswith(ATTRIBUTES_TOPIC):
            self.firmware_info = ujson.loads(msg)

            if '/response/' in topic:
                self._handle_firmware_info()

            if (self.firmware_info.get(FW_VERSION_ATTR) is not None and self.firmware_info.get(
                    FW_VERSION_ATTR) != self.current_firmware_info.get("current_" + FW_VERSION_ATTR)) or \
                    (self.firmware_info.get(FW_TITLE_ATTR) is not None and self.firmware_info.get(
                        FW_TITLE_ATTR) != self.current_firmware_info.get("current_" + FW_TITLE_ATTR)):
                self._handle_firmware_update()

    def _handle_firmware_info(self):
        self.firmware_info = self.firmware_info.get("shared", {}) if isinstance(self.firmware_info,
                                                                                dict) else {}

    def _handle_firmware_update(self):
        print('Firmware is not the same')
        self.firmware_data = b''
        self.__current_chunk = 0

        self.current_firmware_info[FW_STATE_ATTR] = "DOWNLOADING"
        self.send_telemetry(self.current_firmware_info)
        time.sleep(1)

        self.__firmware_request_id = self.__firmware_request_id + 1
        self.__target_firmware_length = self.firmware_info[FW_SIZE_ATTR]
        self.__chunk_count = 0 if not self.__chunk_size else ceil(
            self.firmware_info[FW_SIZE_ATTR] / self.__chunk_size)
        self.__get_firmware()

    def __get_firmware(self):
        payload = '' if not self.__chunk_size or self.__chunk_size > self.firmware_info.get(FW_SIZE_ATTR, 0) else str(
            self.__chunk_size).encode()
        self._client.publish("v2/fw/request/{0}/chunk/{1}".format(self.__firmware_request_id, self.__current_chunk),
                             payload, qos=1)

    def __process_firmware(self):
        self.current_firmware_info[FW_STATE_ATTR] = "DOWNLOADED"
        self.send_telemetry(self.current_firmware_info)
        time.sleep(1)

        verification_result = verify_checksum(self.firmware_data, self.firmware_info.get(FW_CHECKSUM_ALG_ATTR),
                                              self.firmware_info.get(FW_CHECKSUM_ATTR))

        if verification_result:
            print('Checksum verified!')
            self.current_firmware_info[FW_STATE_ATTR] = "VERIFIED"
            self.send_telemetry(self.current_firmware_info)
            time.sleep(1)

            self.__on_firmware_received(self.firmware_info.get(FW_VERSION_ATTR))

            self.current_firmware_info = {
                "current_" + FW_TITLE_ATTR: self.firmware_info.get(FW_TITLE_ATTR),
                "current_" + FW_VERSION_ATTR: self.firmware_info.get(FW_VERSION_ATTR),
                FW_STATE_ATTR: "UPDATED"
            }
            self.send_telemetry(self.current_firmware_info)
        else:
            print('Checksum verification failed!')
            self.current_firmware_info[FW_STATE_ATTR] = "FAILED"
            self.send_telemetry(self.current_firmware_info)
            self.__request_firmware_info()
            return
        self.firmware_received = True

    def __on_firmware_received(self, version_to):
        with open(self.firmware_info.get(FW_TITLE_ATTR), "wb") as firmware_file:
            firmware_file.write(self.firmware_data)
        print('Firmware is updated!\n Current firmware version is: {0}'.format(version_to))
        machine.reset()

    def __request_firmware_info(self):
        self.__request_id = self.__request_id + 1
        self._client.publish("v1/devices/me/attributes/request/{0}".format(self.__request_id),
                             ujson.dumps({"sharedKeys": REQUIRED_SHARED_KEYS}))

    def _handle_rpc_request(self, topic, msg):
        request_id = topic[len(RPC_REQUEST_TOPIC):len(topic)]
        if self.__device_on_server_side_rpc_response:
            self.__device_on_server_side_rpc_response(request_id, ujson.loads(msg))

    def _handle_rpc_response(self, topic, msg):
        request_id = int(topic[len(RPC_RESPONSE_TOPIC):len(topic)])
        callback = self.__device_client_rpc_dict.pop(request_id)
        callback(request_id, ujson.loads(msg), None)

    def set_server_side_rpc_request_handler(self, handler):
        self.__device_on_server_side_rpc_response = handler

    def _handle_attributes(self, msg):
        msg = ujson.loads(msg)
        dict_results = []
        # callbacks for everything
        if self.__device_sub_dict.get("*"):
            for subscription_id in self.__device_sub_dict["*"]:
                dict_results.append(self.__device_sub_dict["*"][subscription_id])
        # specific callback
        keys = msg.keys()
        keys_list = []
        for key in keys:
            keys_list.append(key)
        # iterate through message
        for key in keys_list:
            # find key in our dict
            if self.__device_sub_dict.get(key):
                for subscription in self.__device_sub_dict[key]:
                    dict_results.append(self.__device_sub_dict[key][subscription])
        for res in dict_results:
            res(msg, None)

    def _handle_attribute_response(self, topic, msg):
        req_id = int(topic[len(ATTRIBUTES_TOPIC + "/response/"):])
        callback = self._attr_request_dict.pop(req_id)
        if isinstance(callback, tuple):
            callback[0](ujson.loads(msg), None, callback[1])
        else:
            callback(ujson.loads(msg), None)

    def send_telemetry(self, data):
        telemetry_topic = 'v1/devices/me/telemetry'
        self._client.publish(telemetry_topic, ujson.dumps(data))

    def send_attributes(self, data):
        self._client.publish(ATTRIBUTES_TOPIC, ujson.dumps(data))

    def request_attributes(self, client_keys=None, shared_keys=None, callback=None):
        msg = {}
        if client_keys:
            tmp = ""
            for key in client_keys:
                tmp += key + ","
            tmp = tmp[:len(tmp) - 1]
            msg.update({"clientKeys": tmp})
        if shared_keys:
            tmp = ""
            for key in shared_keys:
                tmp += key + ","
            tmp = tmp[:len(tmp) - 1]
            msg.update({"sharedKeys": tmp})
        self._add_attr_request_callback(callback)
        self._client.publish(ATTRIBUTE_REQUEST_TOPIC + str(self.__attr_request_number),
                             ujson.dumps(msg),
                             qos=self.quality_of_service)
        self._client.wait_msg()

    def _add_attr_request_callback(self, callback):
        self.__attr_request_number += 1
        self._attr_request_dict.update({self.__attr_request_number: callback})
        attr_request_number = self.__attr_request_number
        return attr_request_number

    def send_rpc_call(self, method, params, callback):
        self.__device_client_rpc_number += 1
        self.__device_client_rpc_dict.update({self.__device_client_rpc_number: callback})
        rpc_request_id = self.__device_client_rpc_number
        payload = {"method": method, "params": params}
        self._client.publish(RPC_REQUEST_TOPIC + str(rpc_request_id),
                             ujson.dumps(payload),
                             qos=self.quality_of_service)
        self._client.wait_msg()

    def unsubscribe_from_attribute(self, subscription_id):
        for attribute in self.__device_sub_dict:
            if self.__device_sub_dict[attribute].get(subscription_id):
                del self.__device_sub_dict[attribute][subscription_id]
                print("Unsubscribed from {0}, subscription id {1}".format(attribute, subscription_id))
        if subscription_id == '*':
            self.__device_sub_dict = {}
        self.__device_sub_dict = dict((k, v) for k, v in self.__device_sub_dict.items() if v)

    def clean_device_sub_dict(self):
        self.__device_sub_dict = {}

    def subscribe_to_all_attributes(self, callback):
        return self.subscribe_to_attribute("*", callback)

    def subscribe_to_attribute(self, key, callback):
        self.__device_max_sub_id += 1
        if key not in self.__device_sub_dict:
            self.__device_sub_dict.update({key: {self.__device_max_sub_id: callback}})
        else:
            self.__device_sub_dict[key].update({self.__device_max_sub_id: callback})
        print("Subscribed to {0} with id {1}".format(key, self.__device_max_sub_id))
        return self.__device_max_sub_id

    def wait_for_msg(self):
        self._client.wait_msg()

    @staticmethod
    def provision(host,
                  provision_device_key,
                  provision_device_secret,
                  port=1883,
                  device_name=None,
                  access_token=None,
                  client_id=None,
                  username=None,
                  password=None,
                  hash=None,
                  gateway=None):

        import gc
        gc.collect()
        print(f"Free memory before provisioning: {gc.mem_free()} bytes")

        try:
            provision_request = {
                "provisionDeviceKey": provision_device_key,
                "provisionDeviceSecret": provision_device_secret
            }

            if access_token:
                provision_request["token"] = access_token
                provision_request["credentialsType"] = "ACCESS_TOKEN"
            elif username or password or client_id:
                provision_request["username"] = username
                provision_request["password"] = password
                provision_request["clientId"] = client_id
                provision_request["credentialsType"] = "MQTT_BASIC"
            elif hash:
                provision_request["hash"] = hash
                provision_request["credentialsType"] = "X509_CERTIFICATE"

            if device_name:
                provision_request["deviceName"] = device_name

            if gateway:
                provision_request["gateway"] = gateway

            print(f"Memory before JSON serialization: {gc.mem_free()} bytes")
            provision_request_str = ujson.dumps(provision_request)
            print(f"Memory after JSON serialization: {gc.mem_free()} bytes")

            from provision_client import ProvisionClient
            provision_client = ProvisionClient(host, port, provision_request)
            gc.collect()
            print(f"Memory after client initialization: {gc.mem_free()} bytes")

            provision_client.provision()
            gc.collect()
            print(f"Memory after provisioning call: {gc.mem_free()} bytes")

            if provision_client.credentials:
                print("Provisioning successful. Credentials obtained.")
                return provision_client.credentials
            else:
                print("Provisioning failed. No credentials obtained.")
                return None

        except MemoryError:
            print("MemoryError occurred during provisioning!")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        finally:
            gc.collect()
            print(f"Free memory after provisioning: {gc.mem_free()} bytes")

