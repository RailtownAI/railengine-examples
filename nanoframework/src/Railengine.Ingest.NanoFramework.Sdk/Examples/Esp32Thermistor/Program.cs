using System.Diagnostics;
using System.Threading;
using System.Device.Gpio;
using System.Device.Adc;

namespace Esp32Thermistor
{
    public class Program
    {
        private static readonly int ledBlinkDuration = 500;
        private static readonly int ledPin = 13;

        // Voltage divider: 3.3V -> 10k -> GPIO 32 -> thermistor -> GND
        // GPIO 32 = ADC1 Channel 4 on ESP32
        private static readonly int thermistorAdcChannel = 4;
        private static readonly double fixedResistor = 10000.0;    // 10k ohm
        private static readonly double nominalResistance = 10000.0; // thermistor resistance at 25°C
        private static readonly double nominalTempK = 298.15;       // 25°C in Kelvin
        private static readonly double betaCoefficient = 3950.0;    // typical NTC beta value

        public static void Main()
        {
            var gpio = new GpioController();
            var led = gpio.OpenPin(ledPin, PinMode.Output);

            var adc = new AdcController();
            var thermistorChannel = adc.OpenChannel(thermistorAdcChannel);

            while (true)
            {
                int adcValue = thermistorChannel.ReadValue();
                int maxAdcValue = adc.MaxValue;

                // R_thermistor = R_fixed * adcValue / (maxAdc - adcValue)
                double resistance = fixedResistor * adcValue / (maxAdcValue - adcValue);

                // Beta equation: 1/T = 1/T0 + (1/B) * ln(R/R0)
                double tempK = 1.0 / (1.0 / nominalTempK + System.Math.Log(resistance / nominalResistance) / betaCoefficient);
                double tempC = tempK - 273.15;
                Debug.WriteLine("ADC: " + adcValue + " | Resistance: " + (int)resistance + " ohm | Temp: " + (int)tempC + " C");

                led.Write(PinValue.High);
                Thread.Sleep(ledBlinkDuration);
                led.Write(PinValue.Low);
                Thread.Sleep(ledBlinkDuration);
            }
        }
    }
}
