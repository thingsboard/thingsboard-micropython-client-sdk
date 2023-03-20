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

from random import getrandbits
from hashlib import sha256


def verify_checksum(firmware_data, checksum_alg, checksum):
    if firmware_data is None:
        print('Firmware was not received!')
        return False
    if checksum is None:
        print('Checksum was\'t provided!')
        return False
    checksum_of_received_firmware = None
    print('Checksum algorithm is: %s' % checksum_alg)
    if checksum_alg.lower() == "sha256":
        checksum_of_received_firmware = "".join(["%.2x" % i for i in sha256(firmware_data).digest()])
    else:
        print('Client error. Unsupported checksum algorithm.')

    print(checksum_of_received_firmware)

    return checksum_of_received_firmware == checksum
