try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from pcf8591_async import PCF8591Async


async def main():
    """Run the source ADC/DAC business sequence with one cleanup owner."""
    i2c_bus = None
    sensor = None
    try:
        await asyncio.sleep(3)
        i2c_bus = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
        addresses = i2c_bus.scan()
        address = next((item for item in addresses if 0x48 <= item <= 0x4F), None)
        if address is None:
            raise SystemExit("I2C scan found no PCF8591")
        sensor = PCF8591Async(address, i2c=i2c_bus)
        analog = await sensor.analog_read_async(0)
        voltage = await sensor.voltage_read_async(0, 3.3)
        print("AIN0 Analog Value: {} | Voltage Value: {:.2f} V".format(analog, voltage))
        await sensor.analog_write_async(128)
        while True:
            values = await sensor.analog_read_all_async()
            print("AIN0: {} | AIN1: {} | AIN2: {} | AIN3: {}".format(*values))
            await asyncio.sleep_ms(500)
    finally:
        try:
            if sensor is not None:
                await sensor.disable_output_async()
                await sensor.aclose()
        finally:
            if i2c_bus is not None:
                i2c_bus.deinit()


if __name__ == '__main__':
    asyncio.run(main())
