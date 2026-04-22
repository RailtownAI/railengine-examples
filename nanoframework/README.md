# Embedded Railengine

A **.NET nanoFramework** SDK that sends sensor data to the [Railengine](https://railengine.ai) Ingest API over HTTPS from microcontrollers.

## What It Does

Connects to Wi-Fi, syncs the system clock, and POSTs JSON payloads to your Railengine ingest endpoint over TLS 1.2.

## Supported Platforms

This example was developed for ESP32. For other platforms, please review the documentation for the .NET nanoFramework.

## Requirements

- A supported microcontroller board with Wi-Fi (eg. ESP32-WROOM-32)
- Visual Studio with the [.NET nanoFramework extension](https://docs.nanoframework.net/content/getting-started-guides/getting-started-managed.html)

## Tested Hardware
- ESP32-WROOM-32
  
The sample should work with other ESP32 boards, but check the pin assigments and ADC channel.

## Network
This SDK is network-agnostic. The example uses Wi-Fi but the Ingest Client
works with any network connection.

## Setup

### Configuration

Create a Secrets.cs file in the Examples\Esp32Thermistor directory with the following contents:
```csharp
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
Set the Wi-Fi credentials for your network and obtain the ingest URL and key from your [Railengine configuration](https://cndr.railtown.ai/)
> ⚠️ Do not commit Secrets.cs to version control. Add it to your .gitignore file.

The .NET nanoFramework does not support a X509 certificate store, so the root CA certificate must be provided directly as a base64-encoded ASCII string (PEM). `Secrets.CaRootCertificate` is used for this purpose and it can remain null for dev/test scenarios. Please see the SSL Validation section below to obtain the correct certificate.

### Components

Connect a thermistor to ADC
- Connect one leg of the thermistor to GPIO 32 (which maps to ADC1 Channel 4)
- Connect the other leg to ground
- Add a 10kΩ resistor between GPIO 32 and the 3.3V pin to complete the voltage divider

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
In a production context the current root CA for the ingest server's certificate should be used.
As of April 2026, the correct certificate is the Sectigo Public Server Authentication certificate below. If you encounter SSL validation errors when using this, please obtain the current certificate. Visit the ingest URL in a browser, view the site certificate and export the current *root* certificate.
```text
-----BEGIN CERTIFICATE-----
MIIFijCCA3KgAwIBAgIQdY39i658BwD6qSWn4cetFDANBgkqhkiG9w0BAQwFADBf
MQswCQYDVQQGEwJHQjEYMBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTYwNAYDVQQD
Ey1TZWN0aWdvIFB1YmxpYyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gUm9vdCBSNDYw
HhcNMjEwMzIyMDAwMDAwWhcNNDYwMzIxMjM1OTU5WjBfMQswCQYDVQQGEwJHQjEY
MBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTYwNAYDVQQDEy1TZWN0aWdvIFB1Ymxp
YyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gUm9vdCBSNDYwggIiMA0GCSqGSIb3DQEB
AQUAA4ICDwAwggIKAoICAQCTvtU2UnXYASOgHEdCSe5jtrch/cSV1UgrJnwUUxDa
ef0rty2k1Cz66jLdScK5vQ9IPXtamFSvnl0xdE8H/FAh3aTPaE8bEmNtJZlMKpnz
SDBh+oF8HqcIStw+KxwfGExxqjWMrfhu6DtK2eWUAtaJhBOqbchPM8xQljeSM9xf
iOefVNlI8JhD1mb9nxc4Q8UBUQvX4yMPFF1bFOdLvt30yNoDN9HWOaEhUTCDsG3X
ME6WW5HwcCSrv0WBZEMNvSE6Lzzpng3LILVCJ8zab5vuZDCQOc2TZYEhMbUjUDM3
IuM47fgxMMxF/mL50V0yeUKH32rMVhlATc6qu/m1dkmU8Sf4kaWD5QazYw6A3OAS
VYCmO2a0OYctyPDQ0RTp5A1NDvZdV3LFOxxHVp3i1fuBYYzMTYCQNFu31xR13NgE
SJ/AwSiItOkcyqex8Va3e0lMWeUgFaiEAin6OJRpmkkGj80feRQXEgyDet4fsZfu
+Zd4KKTIRJLpfSYFplhym3kT2BFfrsU4YjRosoYwjviQYZ4ybPUHNs2iTG7sijbt
8uaZFURww3y8nDnAtOFr94MlI1fZEoDlSfB1D++N6xybVCi0ITz8fAr/73trdf+L
HaAZBav6+CuBQug4urv7qv094PPK306Xlynt8xhW6aWWrL3DkJiy4Pmi1KZHQ3xt
zwIDAQABo0IwQDAdBgNVHQ4EFgQUVnNYZJX5khqwEioEYnmhQBWIIUkwDgYDVR0P
AQH/BAQDAgGGMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQEMBQADggIBAC9c
mTz8Bl6MlC5w6tIyMY208FHVvArzZJ8HXtXBc2hkeqK5Duj5XYUtqDdFqij0lgVQ
YKlJfp/imTYpE0RHap1VIDzYm/EDMrraQKFz6oOht0SmDpkBm+S8f74TlH7Kph52
gDY9hAaLMyZlbcp+nv4fjFg4exqDsQ+8FxG75gbMY/qB8oFM2gsQa6H61SilzwZA
Fv97fRheORKkU55+MkIQpiGRqRxOF3yEvJ+M0ejf5lG5Nkc/kLnHvALcWxxPDkjB
JYOcCj+esQMzEhonrPcibCTRAUH4WAP+JWgiH5paPHxsnnVI84HxZmduTILA7rpX
DhjvLpr3Etiga+kFpaHpaPi8TD8SHkXoUsCjvxInebnMMTzD9joiFgOgyY9mpFui
TdaBJQbpdqQACj7LzTWb4OE4y2BThihCQRxEV+ioratF4yUQvNs+ZUH7G6aXD+u5
dHn5HrwdVw1Hr8Mvn4dGp+smWg9WY7ViYG4A++MnESLn/pmPNPW56MORcr3Ywx65
LvKRRFHQV80MNNVIIb/bE/FmJUNS0nAiNs2fxBx1IK1jcmMGDw4nztJqDby1ORrp
0XZ60Vzk50lJLVU3aPAaOpg+VBeHVOmmJ1CJeyAvP/+/oYtKR5j/K3tJPsMpRmAY
QqszKbrAKbkTidOIijlBO8n9pu0f9GBj39ItVQGL
-----END CERTIFICATE-----
```
