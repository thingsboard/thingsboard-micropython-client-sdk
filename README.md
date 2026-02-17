# ThingsBoard MQTT client MicroPython SDK

<p align="center" style="text-align: center">
    <a href="https://thingsboard.io"><img alt="ThingsBoard" src="./logo.png?raw=true" width="128" height="128"></a>
</p>

<p align="center">
ThingsBoard is an open-source IoT platform for data collection, processing, visualization, and device management.
This project is a MicroPython library that provides convenient client SDK for <a href="https://thingsboard.io/docs/reference/mqtt-api/">Device MQTT API</a>.
<br />
<br />

<a href="https://github.com/thingsboard/thingsboard-micropython-client-sdk/blob/main/LICENSE">
    <img alt="Discord" src="https://img.shields.io/badge/license-Apache_2.0-blue" />
</a>
<a href="https://github.com/thingsboard/thingsboard-micropython-client-sdk/issues">
    <img alt="Discord" src="https://img.shields.io/badge/contributions-welcome-green" />
</a>
<a href=https://github.com/thingsboard/thingsboard-micropython-client-sdk/releases/latest">
    <img alt="Discord" src="https://img.shields.io/github/v/release/thingsboard/thingsboard-micropython-client-sdk" />
</a>
<a href="https://discord.gg/mJxDjAM3PF">
    <img alt="Discord" src="https://img.shields.io/discord/1458396495610122526?logo=discord" />
</a>
</p>

**💡 Make the notion that it is the early beta of MicroPython Client SDK. So we 
appreciate any help in improving this project and getting it growing.**

## Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Getting Started](#-getting-started)
- [Documentation](#-documentation)
- [Examples](#-examples)
- [Guides](#-guides)
- [Contributing](#-contributing)
- [Support & Community](#-support--community)
- [Licenses](#-licenses)

## 🧩 Features

- Provided all supported feature of `umqtt` library
- Unencrypted and encrypted (TLS v1.2) connection
- QoS 0 and 1 (MQTT only)
- Automatic reconnect
- [Device MQTT](https://thingsboard.io/docs/reference/mqtt-api/) API provided by ThingsBoard
- Firmware updates
- Device Claiming
- Device provisioning

## 📦 Installation

To install using mip:

```bash
import mip

mip.install('github:thingsboard/thingsboard-micropython-client-sdk')
```

## 🟢 Getting Started

Client initialization and telemetry publishing

```python
from thingsboard_sdk.tb_device_mqtt import TBDeviceMqttClient

telemetry = {"temperature": 41.9, "enabled": False, "currentFirmwareVersion": "v1.2.2"}
client = TBDeviceMqttClient(host="127.0.0.1", access_token="A1_TEST_TOKEN")
# Connect to ThingsBoard
client.connect()
# Sending telemetry without checking the delivery status
client.send_telemetry(telemetry) 
# Disconnect from ThingsBoard
client.disconnect()
```

## 📚 Documentation

You can find the full official documentation [here](https://thingsboard.io/docs/reference/micropython-client-sdk/). It
includes detailed information about the SDK's features, API reference, and usage examples.

## 🪛 Examples

You can find more examples [here](./examples). They demonstrate how to use the SDK to connect to ThingsBoard, send 
telemetry data, subscribe to attribute changes, handle RPC calls, etc.

## 🗺 Guides

- [💡 ESP32 LED Lamp](./examples/esp32_based_led_lamp)

## ⭐ Contributing

We welcome contributions to the ThingsBoard MicroPython Client SDK! If you have an idea for a new feature, 
have found a bug, or want to improve the documentation, please feel free to submit a pull request or open an issue.

## 💬 Support & Community

Need help or want to share ideas?

 - [Join our Discord](https://discord.gg/mJxDjAM3PF)
 - [Stackoverflow](http://stackoverflow.com/questions/tagged/thingsboard)

**🐞 Found a bug?** Please open an issue.

## ⚖️ Licenses

This project is released under [Apache 2.0 License](./LICENSE).
