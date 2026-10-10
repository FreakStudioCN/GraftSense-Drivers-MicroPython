try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from mcp3421_async import I2cAdapterAsync, Mcp342XAsync


async def main():
    """Run finite single-shot and continuous MCP3421 source workflows."""
    i2c_bus = None
    adc = None
    await asyncio.sleep(3)
    try:
        i2c_bus = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
        if 0x68 not in i2c_bus.scan():
            raise SystemExit("I2C scan found no MCP3421")
        adapter = I2cAdapterAsync(i2c_bus)
        adc = Mcp342XAsync(adapter, "mcp3421", 0x68)
        await adc.start_measurement_async(True, 1, 0)
        conversion_us = await adc.get_conversion_cycle_time_async()
        print("---Single measurement mode---")
        for _ in range(33):
            await asyncio.sleep_ms(max(1, (conversion_us + 999) // 1000))
            value = await adc.get_value_async(raw=False)
            print("Voltage: {} Volts".format(value))
            await adc.start_measurement_async(True, 1, 0)
        await adc.start_measurement_async(False, 1, 0)
        conversion_us = await adc.get_conversion_cycle_time_async()
        print("---Automatic ADC measurement mode---")
        for _ in range(33):
            await asyncio.sleep_ms(max(1, (conversion_us + 999) // 1000))
            value = await adc.get_value_async(raw=False)
            print("Voltage: {} Volts".format(value))
    finally:
        try:
            if adc is not None:
                await adc.aclose()
        finally:
            if i2c_bus is not None:
                i2c_bus.deinit()

if __name__ == '__main__':
    asyncio.run(main())
