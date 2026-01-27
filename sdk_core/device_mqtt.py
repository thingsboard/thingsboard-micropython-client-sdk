from ubinascii import hexlify
from machine import unique_id, reset
from ujson import dumps, loads
from time import sleep

from .sdk_utils import verify_checksum

FW_TITLE_ATTR = "fw_title"
FW_VERSION_ATTR = "fw_version"
FW_CHECKSUM_ATTR = "fw_checksum"
FW_CHECKSUM_ALG_ATTR = "fw_checksum_algorithm"
FW_SIZE_ATTR = "fw_size"
FW_STATE_ATTR = "fw_state"

RPC_REQUEST_TOPIC = 'v1/devices/me/rpc/request/'
RPC_RESPONSE_TOPIC = 'v1/devices/me/rpc/response/'
ATTRIBUTES_TOPIC = 'v1/devices/me/attributes'
ATTRIBUTE_REQUEST_TOPIC = 'v1/devices/me/attributes/request/'
ATTRIBUTE_TOPIC_RESPONSE = 'v1/devices/me/attributes/response/'
CLAIMING_TOPIC = "v1/devices/me/claim"
REQUIRED_SHARED_KEYS = "{0},{1},{2},{3},{4}".format(
    FW_CHECKSUM_ATTR, FW_CHECKSUM_ALG_ATTR, FW_SIZE_ATTR, FW_TITLE_ATTR, FW_VERSION_ATTR
)


class TBDeviceMqttClientBase:
    def __init__(self, mqtt_client, host, port=1883, access_token=None, quality_of_service=None, client_id=None,
                 chunk_size=0):
        self._host = host
        self._port = port
        self.quality_of_service = quality_of_service if quality_of_service is not None else 1
        self.current_firmware_info = {
            "current_" + FW_TITLE_ATTR: "Initial",
            "current_" + FW_VERSION_ATTR: "v0"
        }
        self.firmware_info = None
        self.__current_chunk = None
        self.firmware_data = None
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
            client_id = hexlify(unique_id())
        self._client_id = client_id
        self._client = mqtt_client

    def __subscribe_all_required_topics(self):
        self._client.subscribe(ATTRIBUTES_TOPIC, qos=self.quality_of_service)
        self._client.subscribe(ATTRIBUTES_TOPIC + "/response/+", qos=self.quality_of_service)
        self._client.subscribe(RPC_REQUEST_TOPIC + '+', qos=self.quality_of_service)
        self._client.subscribe(RPC_RESPONSE_TOPIC + '+', qos=self.quality_of_service)

    def disconnect(self):
        self._client.disconnect()
        self.connected = False

    def connect(self):
        print('Unimplemented due to different inner logic realisation')

    def send_telemetry(self, data):
        telemetry_topic = 'v1/devices/me/telemetry'
        self._client.publish(telemetry_topic, dumps(data))

    def send_attributes(self, data):
        self._client.publish(ATTRIBUTES_TOPIC, dumps(data))

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
        self.__attr_request_number += 1
        self._attr_request_dict.update({self.__attr_request_number: callback})
        self._client.publish(ATTRIBUTE_REQUEST_TOPIC + str(self.__attr_request_number),
                             dumps(msg),
                             qos=self.quality_of_service)

    def send_rpc_call(self, method, params, callback):
        self.__device_client_rpc_number += 1
        self.__device_client_rpc_dict.update({self.__device_client_rpc_number: callback})
        rpc_request_id = self.__device_client_rpc_number
        payload = {"method": method, "params": params}
        self._client.publish(RPC_REQUEST_TOPIC + str(rpc_request_id),
                             dumps(payload),
                             qos=self.quality_of_service)

    def set_server_side_rpc_request_handler(self, handler):
        self.__device_on_server_side_rpc_response = handler

    def claim_device(self, secret_key=None, duration_ms=None):
        claim_request = {}
        if secret_key:
            claim_request["secretKey"] = secret_key
        if duration_ms:
            claim_request["durationMs"] = duration_ms

        payload = dumps(claim_request)
        print(f"Sending claim request to topic '{CLAIMING_TOPIC}' with payload: {payload}")
        self._client.publish(CLAIMING_TOPIC, payload, qos=self.quality_of_service)

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

    def unsubscribe_from_attribute(self, subscription_id):
        for attribute in self.__device_sub_dict:
            if self.__device_sub_dict[attribute].get(subscription_id):
                del self.__device_sub_dict[attribute][subscription_id]
                print("Unsubscribed from {0}, subscription id {1}".format(attribute, subscription_id))
        if subscription_id == '*':
            self.__device_sub_dict = {}
        self.__device_sub_dict = dict((k, v) for k, v in self.__device_sub_dict.items() if v)

    def all_subscribed_topics_callback(self, topic, msg):
        topic = topic.decode('utf-8')
        print('callback', topic, msg)

        update_response_pattern = "v2/fw/response/" + str(self.__firmware_request_id) + "/chunk/"

        if topic.startswith(update_response_pattern):
            firmware_data = msg

            self.firmware_data = self.firmware_data + firmware_data
            self.__current_chunk = self.__current_chunk + 1

            print('Getting chunk with number: %s. Chunk size is : %r byte(s).' % (
                self.__current_chunk, self.__chunk_size
            ))

            if len(self.firmware_data) == self.__target_firmware_length:
                self.__process_firmware()
            else:
                self.__get_firmware()
        else:
            self._on_decode_message(topic, msg)

    def _on_decode_message(self, topic, msg):
        if topic.startswith(RPC_REQUEST_TOPIC):
            request_id = topic[len(RPC_REQUEST_TOPIC):len(topic)]
            if self.__device_on_server_side_rpc_response:
                self.__device_on_server_side_rpc_response(request_id, loads(msg))
        elif topic.startswith(RPC_RESPONSE_TOPIC):
            request_id = int(topic[len(RPC_RESPONSE_TOPIC):len(topic)])
            callback = self.__device_client_rpc_dict.pop(request_id)
            callback(request_id, loads(msg), None)
        elif topic == ATTRIBUTES_TOPIC:
            msg = loads(msg)
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
        elif topic.startswith(ATTRIBUTE_TOPIC_RESPONSE):
            req_id = int(topic[len(ATTRIBUTES_TOPIC + "/response/"):])
            callback = self._attr_request_dict.pop(req_id)
            if isinstance(callback, tuple):
                callback[0](loads(msg), None, callback[1])
            else:
                callback(loads(msg), None)

        if topic.startswith(ATTRIBUTES_TOPIC):
            self.firmware_info = loads(msg)

            if '/response/' in topic:
                self.firmware_info = self.firmware_info.get("shared", {}) if isinstance(self.firmware_info, dict) else {}

            if (self.firmware_info.get(FW_VERSION_ATTR) is not None and self.firmware_info.get(
                    FW_VERSION_ATTR) != self.current_firmware_info.get("current_" + FW_VERSION_ATTR)) or \
                    (self.firmware_info.get(FW_TITLE_ATTR) is not None and self.firmware_info.get(
                        FW_TITLE_ATTR) != self.current_firmware_info.get("current_" + FW_TITLE_ATTR)):
                print('Firmware is not the same')
                self.firmware_data = b''
                self.__current_chunk = 0

                self.current_firmware_info[FW_STATE_ATTR] = "DOWNLOADING"
                self.send_telemetry(self.current_firmware_info)
                sleep(1)

                self.__firmware_request_id = self.__firmware_request_id + 1
                self.__target_firmware_length = self.firmware_info[FW_SIZE_ATTR]
                firmware_tail = 0 if not self.__chunk_size else self.firmware_info[FW_SIZE_ATTR] % self.__chunk_size
                self.__chunk_count = 0 if not self.__chunk_size else int(
                    self.firmware_info[FW_SIZE_ATTR] / self.__chunk_size) + (0 if not firmware_tail else 1)
                self.__get_firmware()

    def __get_firmware(self):
        payload = '' if not self.__chunk_size or self.__chunk_size > self.firmware_info.get(FW_SIZE_ATTR, 0) else str(
            self.__chunk_size).encode()
        self._client.publish("v2/fw/request/{0}/chunk/{1}".format(self.__firmware_request_id, self.__current_chunk),
                             payload, qos=1)

    def __process_firmware(self):
        self.current_firmware_info[FW_STATE_ATTR] = "DOWNLOADED"
        self.send_telemetry(self.current_firmware_info)
        sleep(1)

        verification_result = verify_checksum(self.firmware_data, self.firmware_info.get(FW_CHECKSUM_ALG_ATTR),
                                              self.firmware_info.get(FW_CHECKSUM_ATTR))

        if verification_result:
            print('Checksum verified!')
            self.current_firmware_info[FW_STATE_ATTR] = "VERIFIED"
            self.send_telemetry(self.current_firmware_info)
            sleep(1)

            with open(self.firmware_info.get(FW_TITLE_ATTR), "wb") as firmware_file:
                firmware_file.write(self.firmware_data)

            self.current_firmware_info = {
                "current_" + FW_TITLE_ATTR: self.firmware_info.get(FW_TITLE_ATTR),
                "current_" + FW_VERSION_ATTR: self.firmware_info.get(FW_VERSION_ATTR),
                FW_STATE_ATTR: "UPDATED"
            }
            self.send_telemetry(self.current_firmware_info)
            print('Firmware is updated!\n Current firmware version is: {0}'.format(self.firmware_info.get(FW_VERSION_ATTR)))
            self.firmware_received = True
            reset()
        else:
            print('Checksum verification failed!')
            self.current_firmware_info[FW_STATE_ATTR] = "FAILED"
            self.send_telemetry(self.current_firmware_info)
            self.__request_id = self.__request_id + 1
            self._client.publish("v1/devices/me/attributes/request/{0}".format(self.__request_id),
                                 dumps({"sharedKeys": REQUIRED_SHARED_KEYS}))
            return
