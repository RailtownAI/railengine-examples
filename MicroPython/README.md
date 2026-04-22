# Embedded Railengine

A **MicroPython** SDK that sends sensor data to the [Railengine](https://railengine.ai) Ingest API over HTTPS from microcontrollers.

## What It Does

Connects to WiFi, syncs the system clock, and POSTs JSON payloads to your Railengine ingest endpoint over TLS 1.2.

## Supported Platforms

This example was developed for ESP32. For other platforms, please review the documentation for MicroPython.

## Requirements

- A supported microcontroller board with WiFi (eg. ESP32-WROOM-32)
- A Python IDE with MicroPython device support (eg. Thonny)

## Tested Hardware
- ESP32-WROOM-32
  
The sample should work with other ESP32 boards, but check the pin assigments.

## Network
This SDK is network-agnostic. The example uses WiFi but the Ingest Client
works with any network connection. 

## Setup

### Configuration

Create a secrets.py file with the following contents:
```python
WIFI_SSID = ""
WIFI_PASSWORD = ""
# == ENGINE INGEST API URL ==
API_URL = ""
# == ENGINE INGEST API KEY ==
API_KEY = ""
```
Set the Wi-Fi credentials for your network and obtain the ingest URL and key from your [Railengine configuration](https://cndr.railtown.ai/)
> ⚠️ Do not commit secrets.py to version control. Add it to your .gitignore file.

### Components

Connect a thermistor to ADC
- Connect one leg of the thermistor to GPIO 32
- Connect the other leg to ground
- Add a 10kΩ resistor between GPIO 32 and the 3.3V pin to complete the voltage divider

LEDs:
- Pin 13: Error indicator LED with grounded cathode (required if you want visual feedback)
- Pin 2: This is the onboard LED for the ESP32-WROOM-32 and the sample uses it to indicate when the Ingest Client is active

All of these pins can be changed at the top of main.py

## Payload Format

This example uses a specific JSON payload, but Railengine can accept any JSON document. To adapt the example for your payload update the template used for `ingestor.send`.
