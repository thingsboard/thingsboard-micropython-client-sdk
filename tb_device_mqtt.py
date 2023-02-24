from umqtt import MQTTClient, MQTTException
import ujson
import ubinascii
import machine


class TBDeviceMqttClient:
    def __init__(self, host, port=1883, access_token=None, quality_of_service=None, client_id=None):
        self._host = host
        self._port = port
        self.quality_of_service = quality_of_service if quality_of_service is not None else 1
        self.rpc_request_topic = 'v1/devices/me/rpc/request/+'
        self.attributes_topic = 'v1/devices/me/attributes'
        self.attribute_request_topic = 'v1/devices/me/attributes/request'
        self.callbacks = {}
        self.connected = False

        if not access_token:
            print("token is not set, connection without tls wont be established")
        self._access_token = access_token

        if not client_id:
            client_id = ubinascii.hexlify(machine.unique_id())
        self._client_id = client_id
        self._client = MQTTClient(self._client_id, self._host, self._port, self._access_token, 'pswd', keepalive=120)

    def connect(self):
        self._client.set_callback(self._callback)

        try:
            response = self._client.connect()
            self._client.subscribe(self.rpc_request_topic)
            self._client.subscribe(self.attribute_request_topic + '/+')

            self.connected = True

            return response
        except MQTTException as e:
            self.connected = False
            print(e)

    def disconnect(self):
        self._client.disconnect()
        self.connected = False

    def _callback(self, topic, msg):
        if topic == self.rpc_request_topic:
            self._handle_rpc_request(msg)
        elif topic == self.attributes_topic:
            self._handle_attributes(msg)
        elif topic.startswith(self.attribute_request_topic):
            self._handle_attribute_request(topic, msg)

    def _handle_rpc_request(self, msg):
        try:
            data = ujson.loads(msg)
            request_id = data['id']
            method = data['method']
            params = data.get('params')
            if method in self.callbacks:
                result = self.callbacks[method](params)
            else:
                result = {'error': 'Unknown method: {}'.format(method)}
            response = {
                'id': request_id,
                'data': result
            }
            self._client.publish('v1/devices/me/rpc/response/', ujson.dumps(response))
        except Exception as e:
            print('Error handling RPC request: {}'.format(e))

    def _handle_attributes(self, msg):
        try:
            data = ujson.loads(msg)
            for key in data:
                if key in self.callbacks:
                    self.callbacks[key](data[key])
        except Exception as e:
            print('Error handling attributes message: {}'.format(e))

    def _handle_attribute_request(self, topic, msg):
        try:
            data = ujson.loads(msg)
            request_id = data['id']
            client_keys = data['clientKeys']
            server_keys = self.callbacks['attribute_request'](client_keys)
            response = {
                'id': request_id,
                'data': server_keys
            }
            self._client.publish(topic.replace('request', 'response'), ujson.dumps(response))
        except Exception as e:
            print('Error handling attribute request: {}'.format(e))

    def send_telemetry(self, data):
        telemetry_topic = 'v1/devices/me/telemetry'
        self._client.publish(telemetry_topic, ujson.dumps(data))

    def send_attributes(self, data):
        self._client.publish(self.attributes_topic, ujson.dumps(data))

    def request_attributes(self, client_keys, request_id):
        request = {
            'id': request_id,
            'clientKeys': client_keys
        }
        self._client.publish(self.attribute_request_topic, ujson.dumps(request))
