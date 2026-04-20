using System.Collections;
using System.Diagnostics;
using System.Threading;
using System.Device.Gpio;
using System.Device.Adc;
using nanoFramework.Networking;
using System.Net.NetworkInformation;
using Railengine.Ingest.NanoFramework.Sdk;
using System.Security.Cryptography.X509Certificates;
using System;

namespace Esp32Thermistor
{
    public class Program
    {
        private static readonly int ledPin = 2;
        private static readonly int led2Pin = 13;

        // Voltage divider: 3.3V -> 10k -> GPIO 32 -> thermistor -> GND
        // GPIO 32 = ADC1 Channel 4 on ESP32
        private static readonly int thermistorAdcChannel = 4;
        private static readonly double fixedResistor = 10000.0;    // 10k ohm
        private static readonly double nominalResistance = 10000.0; // thermistor resistance at 25°C
        private static readonly double nominalTempK = 298.15;       // 25°C in Kelvin
        private static readonly double betaCoefficient = 3950.0;    // typical NTC beta value

        // Create a Secrets.cs file to define these values and it will be ignored by git
        private static readonly string ingestApiUrl = Secrets.IngestApiUrl;
        private static readonly string ingestApiKey = Secrets.IngestApiKey;
        private static readonly string wifiSsid = Secrets.WifiSsid;
        private static readonly string wifiPassword = Secrets.WifiPassword;

        private static string location = "home";
        private static readonly string sku = "ESP32-Therm-DNN";

        public static void Main()
        {

            var gpio = new GpioController();
            var led = gpio.OpenPin(ledPin, PinMode.Output);
            var led2 = gpio.OpenPin(led2Pin, PinMode.Output);
            led.Write(PinValue.Low);
            led2.Write(PinValue.Low);

            try
            {
                var wifiConfig = Wireless80211Configuration.GetAllWireless80211Configurations()[0];
                wifiConfig.Ssid = wifiSsid;
                wifiConfig.Password = wifiPassword;
                wifiConfig.Options = Wireless80211Configuration.ConfigurationOptions.Enable |
                                     Wireless80211Configuration.ConfigurationOptions.AutoConnect;
                wifiConfig.SaveConfiguration();

                Debug.WriteLine($"Connecting to WiFI network: {wifiConfig.Ssid}...");
                var cts = new CancellationTokenSource(60000);
                NetworkHelper.SetupAndConnectNetwork(cts.Token, requiresDateTime: true);

                var wifiAttempts = 10;

                while (NetworkHelper.Status != NetworkHelperStatus.NetworkIsReady && wifiAttempts-- > 0)
                {
                    Debug.WriteLine("Network failed: " + NetworkHelper.Status.ToString());
                    led2.Write(PinValue.High);
                    Thread.Sleep(200);
                }
                led2.Write(PinValue.Low);

                var ip = NetworkInterface.GetAllNetworkInterfaces()[0].IPv4Address;
                location = "home (" + ip + ")";
                Debug.WriteLine("WiFi connected, clock synced. IP: " + ip);

                var adc = new AdcController();
                var thermistorChannel = adc.OpenChannel(thermistorAdcChannel);

                X509Certificate caCert = null;
                var client = new IngestClient(ingestApiUrl, ingestApiKey, caCert);

                while (true)
                {
                    int adcValue = thermistorChannel.ReadValue();
                    int maxAdcValue = adc.MaxValue;

                    // R_thermistor = R_fixed * adcValue / (maxAdc - adcValue)
                    double resistance = fixedResistor * adcValue / (maxAdcValue - adcValue);

                    // Beta equation: 1/T = 1/T0 + (1/B) * ln(R/R0)
                    double tempK = 1.0 / (1.0 / nominalTempK + Math.Log(resistance / nominalResistance) / betaCoefficient);
                    double tempC = tempK - 273.15;

                    Debug.WriteLine("ADC: " + adcValue + " | Resistance: " + (int)resistance + " ohm | Temp: " + (int)tempC + " C");

                    var payload = new Hashtable
                    {
                        { "c", (int)tempC },
                        { "timestamp", DateTime.UtcNow.ToString("o") },
                        { "rh", "0" },
                        { "light", "0" },
                        { "location", location },
                        { "sku", sku }
                    };

                    led.Write(PinValue.High);
                    client.Send(payload);
                    led.Write(PinValue.Low);

                    Thread.Sleep(300000);
                }
            } 
            catch (Exception ex)
            {
                Debug.WriteLine("Failed: " + ex.ToString());
                led2.Write(PinValue.High);
                return;
            }
        }
    }
}
