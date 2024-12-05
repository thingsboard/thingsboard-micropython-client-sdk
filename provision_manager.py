import gc
import ujson
from provision_client import ProvisionClient

class ProvisionManager:


    def __init__(self, host, port=1883):
        self.host = host
        self.port = port
        self.credentials = None

    def provision_device(self,
                         provision_device_key,
                         provision_device_secret,
                         device_name=None,
                         access_token=None,
                         client_id=None,
                         username=None,
                         password=None,
                         hash=None,
                         gateway=None):

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

            provision_client = ProvisionClient(self.host, self.port, provision_request)
            gc.collect()
            print(f"Memory after client initialization: {gc.mem_free()} bytes")

            provision_client.provision()
            gc.collect()
            print(f"Memory after provisioning call: {gc.mem_free()} bytes")

            if provision_client.credentials:
                print("Provisioning successful. Credentials obtained.")
                self.credentials = provision_client.credentials
                return self.credentials
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
