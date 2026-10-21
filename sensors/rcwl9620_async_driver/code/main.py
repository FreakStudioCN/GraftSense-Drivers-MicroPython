"""RCWL9620 asynchronous distance-sensor demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from rcwl9620_async import RCWL9620Async

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
SENSOR_ADDR = 0x57
READ_INTERVAL_MS = 1000


async def main():
    await asyncio.sleep_ms(3000)
    i2c = None
    sensor = None
    try:
        i2c = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        if SENSOR_ADDR not in i2c.scan():
            raise RuntimeError('RCWL9620 not found')
        sensor = RCWL9620Async(i2c=i2c, address=SENSOR_ADDR)
        while True:
            print('Distance: %.2f mm' % await sensor.read_async())
            await asyncio.sleep_ms(READ_INTERVAL_MS)
    finally:
        if sensor is not None:
            await sensor.deinit_async()
        if i2c is not None and hasattr(i2c, 'deinit'):
            i2c.deinit()


asyncio.run(main())