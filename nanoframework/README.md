# Embedded Railengine

A **.NET nanoFramework** SDK that sends sensor data to the [Railengine](https://railengine.ai) Ingest API over HTTPS from microcontrollers.

## What It Does

Connects to WiFi, syncs the system clock, and POSTs JSON payloads to your Railengine ingest endpoint over TLS 1.2.

## Supported Platforms

This example was developed for ESP32. For other platforms, please review the documentation for the .NET nanoFramework.

## Requirements

- A supported microcontroller board with WiFi (eg. ESP32-WROOM-32)
- Visual Studio with the [.NET nanoFramework extension](https://docs.nanoframework.net/content/getting-started-guides/getting-started-managed.html)

## Tested Hardware
- ESP32-WROOM-32
  
The sample should work with other ESP32 boards, but check the pin assigments.

## Network
This SDK is network-agnostic. The examples use WiFi but the Ingest Client
works with any network connection. 

## Setup

### Configuration

Create a Secrets.cs file in the same directory as Program.cs with the following contents:
```
namespace Esp32Thermistor
{
    internal class Secrets
    {
        public const string IngestApiUrl = "";
        public const string IngestApiKey = "";
        public const string WifiSsid = "";
        public const string WifiPassword = "";
        public const string CaRootCertificate = null;
    }
}
```
Use the WiFi credentials for your network and obtain the ingest url and key from your [Railengine configuration](https://cndr.railtown.ai/)
> ⚠️ Do not commit Secrets.cs to version control. Add it to your .gitignore file.

nanoFramework does not support a X509 certificate store, so the root CA certificate must be provided directly as a Base64-encoded ASCII string (PEM). `Secrets.CaRootCertificate` is used for this purpose and it can remain null for dev/test scenarios. Please see the SSL Validation section below to obtain the correct certificate. 

### Components

Connect a thermistor to pin 32
- To create a voltage divider, add a 10kΩ resistor between the thermistor and pin 32.

LEDs:
- Pin 13: Error indicator LED with grounded cathode (required if you want visual feedback)
- Pin 2: This is the onboard LED for the ESP32-WROOM-32 and the sample uses it to indicate when the Ingest Client is active 

All of these pins can be changed at the top of Program.cs

## Payload Format

This example uses a specific JSON payload, but Railengine can accept any JSON document. To adapt the example for your payload:
- pass a Hashtable of values to the Send method
- The client's `JsonBuilder` supports Hashtables containing primitive values or arrays of primitives
- For nested objects or multi-dimensional arrays, use the `Send(string jsonData)` overload, which accepts raw JSON.

## SSL Validation
In a production context the current, root CA for the ingest server's certificate should be used.
As of April 2026, the correct certificate is the Sectigo Public Server Authentication but if you encounter SSL validation errors, please obtain the current certificate. visit the ingest url in a browser, view the site certificate and export the current *root* certificate.
```
-----BEGIN CERTIFICATE-----\nMIIFijCCA3KgAwIBAgIQdY39i658BwD6qSWn4cetFDANBgkqhkiG9w0BAQwFADBf\nMQswCQYDVQQGEwJHQjEYMBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTYwNAYDVQQD\nEy1TZWN0aWdvIFB1YmxpYyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gUm9vdCBSNDYw\nHhcNMjEwMzIyMDAwMDAwWhcNNDYwMzIxMjM1OTU5WjBfMQswCQYDVQQGEwJHQjEY\nMBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTYwNAYDVQQDEy1TZWN0aWdvIFB1Ymxp\nYyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gUm9vdCBSNDYwggIiMA0GCSqGSIb3DQEB\nAQUAA4ICDwAwggIKAoICAQCTvtU2UnXYASOgHEdCSe5jtrch/cSV1UgrJnwUUxDa\nef0rty2k1Cz66jLdScK5vQ9IPXtamFSvnl0xdE8H/FAh3aTPaE8bEmNtJZlMKpnz\nSDBh+oF8HqcIStw+KxwfGExxqjWMrfhu6DtK2eWUAtaJhBOqbchPM8xQljeSM9xf\niOefVNlI8JhD1mb9nxc4Q8UBUQvX4yMPFF1bFOdLvt30yNoDN9HWOaEhUTCDsG3X\nME6WW5HwcCSrv0WBZEMNvSE6Lzzpng3LILVCJ8zab5vuZDCQOc2TZYEhMbUjUDM3\nIuM47fgxMMxF/mL50V0yeUKH32rMVhlATc6qu/m1dkmU8Sf4kaWD5QazYw6A3OAS\nVYCmO2a0OYctyPDQ0RTp5A1NDvZdV3LFOxxHVp3i1fuBYYzMTYCQNFu31xR13NgE\nSJ/AwSiItOkcyqex8Va3e0lMWeUgFaiEAin6OJRpmkkGj80feRQXEgyDet4fsZfu\n+Zd4KKTIRJLpfSYFplhym3kT2BFfrsU4YjRosoYwjviQYZ4ybPUHNs2iTG7sijbt\n8uaZFURww3y8nDnAtOFr94MlI1fZEoDlSfB1D++N6xybVCi0ITz8fAr/73trdf+L\nHaAZBav6+CuBQug4urv7qv094PPK306Xlynt8xhW6aWWrL3DkJiy4Pmi1KZHQ3xt\nzwIDAQABo0IwQDAdBgNVHQ4EFgQUVnNYZJX5khqwEioEYnmhQBWIIUkwDgYDVR0P\nAQH/BAQDAgGGMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQEMBQADggIBAC9c\nmTz8Bl6MlC5w6tIyMY208FHVvArzZJ8HXtXBc2hkeqK5Duj5XYUtqDdFqij0lgVQ\nYKlJfp/imTYpE0RHap1VIDzYm/EDMrraQKFz6oOht0SmDpkBm+S8f74TlH7Kph52\ngDY9hAaLMyZlbcp+nv4fjFg4exqDsQ+8FxG75gbMY/qB8oFM2gsQa6H61SilzwZA\nFv97fRheORKkU55+MkIQpiGRqRxOF3yEvJ+M0ejf5lG5Nkc/kLnHvALcWxxPDkjB\nJYOcCj+esQMzEhonrPcibCTRAUH4WAP+JWgiH5paPHxsnnVI84HxZmduTILA7rpX\nDhjvLpr3Etiga+kFpaHpaPi8TD8SHkXoUsCjvxInebnMMTzD9joiFgOgyY9mpFui\nTdaBJQbpdqQACj7LzTWb4OE4y2BThihCQRxEV+ioratF4yUQvNs+ZUH7G6aXD+u5\ndHn5HrwdVw1Hr8Mvn4dGp+smWg9WY7ViYG4A++MnESLn/pmPNPW56MORcr3Ywx65\nLvKRRFHQV80MNNVIIb/bE/FmJUNS0nAiNs2fxBx1IK1jcmMGDw4nztJqDby1ORrp\n0XZ60Vzk50lJLVU3aPAaOpg+VBeHVOmmJ1CJeyAvP/+/oYtKR5j/K3tJPsMpRmAY\nQqszKbrAKbkTidOIijlBO8n9pu0f9GBj39ItVQGL\n-----END CERTIFICATE-----
```
