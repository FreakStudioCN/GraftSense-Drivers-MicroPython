try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import ADC, I2C, Pin
from mcp4728_async import MCP4728Async


async def main():
    """Verify channel B through explicit async DAC property operations."""
    i2c_bus = None
    dac = None
    try:
        await asyncio.sleep(3)
        i2c_bus = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
        if 0x60 not in i2c_bus.scan():
            raise SystemExit("I2C scan found no MCP4728")
        dac = MCP4728Async(i2c_bus, 0x60)
        adc = ADC(Pin(26))
        for value in (4095, 2048):
            await dac.b.set_value_async(value)
            await asyncio.sleep_ms(100)
            voltage = adc.read_u16() * 3.3 / 65535
            print("DAC Channel B set to {} -> Actual voltage: {:.2f}V".format(value, voltage))
        await dac.b.set_normalized_value_async(0.5)
        await dac.b.set_vref_async(1)
        await dac.b.set_gain_async(2)
        await dac.save_settings_async()
        print("Channel B: pdm={} vref={} gain={}".format(
            await dac.b.get_pdm_async(), await dac.b.get_vref_async(), await dac.b.get_gain_async()))
    finally:
        try:
            if dac is not None:
                await dac.aclose()
        finally:
            if i2c_bus is not None:
                i2c_bus.deinit()


if __name__ == '__main__':
    asyncio.run(main())
