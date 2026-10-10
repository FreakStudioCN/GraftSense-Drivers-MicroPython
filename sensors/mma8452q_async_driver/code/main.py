try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from mma8452q_async import MMA8452QAsync

async def main():
    i2c_bus = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
        address = next((value for value in i2c_bus.scan() if value in (0x1C, 0x1D)), None)
        if address is None:
            raise RuntimeError('MMA8452Q not found')
        sensor = MMA8452QAsync(i2c=i2c_bus, address=address)
        for rate in sensor.data_rate_values:
            await sensor.data_rate_async(rate)
            acceleration = await sensor.acceleration_async()
            print('rate=%s acceleration=%s' % (rate, acceleration))
            await asyncio.sleep_ms(500)
    finally:
        if sensor is not None:
            await sensor.aclose()
        deinit = getattr(i2c_bus, 'deinit', None)
        if deinit is not None:
            deinit()
if __name__ == '__main__':
    asyncio.run(main())