try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import array

from machine import Pin
from cs1237_async import CS1237Async


def adc_to_voltage(value):
    return value * 1.25 / 8388607


async def main():
    """Run bounded source workflows; DRDY IRQ only sets the adapter ready flag."""
    await asyncio.sleep(3)
    adc = CS1237Async(Pin(5, Pin.OUT), Pin(4, Pin.IN), gain=1, rate=10, channel=0)
    try:
        await adc.initialize_async(timeout_ms=2500)
        print("Configuration:", await adc.get_config_async())
        for index in range(5):
            value = await adc.read_async(timeout_ms=2500)
            print("Read {}: {} -> {:.3f} V".format(index + 1, value, adc_to_voltage(value)))
            await asyncio.sleep_ms(500)
        await adc.config_async(gain=1, rate=40)
        values = array.array("i", [0] * 10)
        await adc.read_buffered_async(values, timeout_ms=2500)
        await adc.calibrate_temperature_async(25.0)
        print("Temperature: {:.2f} C".format(await adc.temperature_async()))
        await adc.power_down_async()
        await asyncio.sleep(2)
        await adc.power_up_async()
    finally:
        await adc.aclose()


if __name__ == '__main__':
    asyncio.run(main())
