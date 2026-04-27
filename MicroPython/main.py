import math
import secrets
from time import sleep, time

import network
import ntptime
from machine import ADC, Pin

from railengine_ingest import RailengineIngest

BUSY_LED_PIN = 2
ERROR_LED_PIN = 13
THERMISTOR_PIN = 32

BETA = 3950  # from thermistor datasheet
R_NOMINAL = 10000  # resistance at 25°C
T_NOMINAL = 25  # nominal temp (°C)
R_SERIES = 10000  # series resistor value
# BETA and R_SERIES can be off so calibrate against a known temperature
OFFSET = -2.0

# MicroPython epoch starts 2000-01-01
# Offset converts to Unix epoch (1970-01-01)
EPOCH_OFFSET = 946684800

adc = ADC(Pin(THERMISTOR_PIN))
busy_led = Pin(BUSY_LED_PIN, Pin.OUT)
error_led = Pin(ERROR_LED_PIN, Pin.OUT)

ingestor = RailengineIngest(
    secrets.API_URL, # pylint: disable=no-member
    secrets.API_KEY # pylint: disable=no-member
)

SENSOR_SKU = "ESP32-Therm-MiP"
LOCATION_DESCRIPTION = "home"


def main():
    ip_address = None
    error_led.off()

    while True:
        try:
            if not ip_address:
                ip_address = connect_wifi()

            a = adc.read()
            t = adc_to_celsius(a)

            print(f"ADC: {a}, Temp: {t}")
            busy_led.on()
            print("Sending data")
            status = ingestor.send(
                {
                    "c": t,
                    "timestamp": (time() + EPOCH_OFFSET) * 1000,
                    "location": f"{LOCATION_DESCRIPTION} '{ip_address}'",
                    "sku": SENSOR_SKU,
                }
            )
            print(f"Status: {status}")
            busy_led.off()
        except Exception as e:
            print(f"Error: {e}")
            for _ in range(10):
                error_led.value(not error_led.value())
                sleep(0.2)

        sleep(30)


def connect_wifi():
    """Connect to WiFi and return IP address"""
    print("Connecting to Wi-Fi...")

    wlan = network.WLAN(network.STA_IF)

    # Reset the interface if it's in a bad state
    if wlan.isconnected():
        print(f"Already connected: {wlan.ifconfig()[0]}")
        return wlan.ifconfig()[0]

    # Force a clean reset before attempting connection
    wlan.active(False)
    sleep(1)
    wlan.active(True)
    sleep(0.5)

    wlan.connect(
        secrets.WIFI_SSID, # pylint: disable=no-member
        secrets.WIFI_PASSWORD # pylint: disable=no-member
    )

    # Wait for connection (max 10 seconds)
    timeout = 10
    while not wlan.isconnected() and timeout > 0:
        busy_led.value(not busy_led.value())  # Blink while connecting
        sleep(0.5)
        timeout -= 0.5

    busy_led.off()

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Connected! IP: {ip}")
        try:
            ntptime.settime()
            print("Time synced:", time())
        except Exception as e:
            print(f"NTP sync failed (non-fatal): {e}")
        return ip
    else:
        print("Wi-Fi connection failed")
        error_led.on()
        return None


def adc_to_celsius(adc_val):
    voltage = adc_val / 4095.0
    resistance = R_SERIES * voltage / (1.0 - voltage)
    steinhart = math.log(resistance / R_NOMINAL) / BETA
    steinhart += 1.0 / (T_NOMINAL + 273.15)
    return (1.0 / steinhart) - 273.15 + OFFSET


try:
    main()
except Exception as e:
    print(f"Fatal error: {e}")
    for _ in range(10):
        error_led.value(not error_led.value())
        sleep(0.2)
