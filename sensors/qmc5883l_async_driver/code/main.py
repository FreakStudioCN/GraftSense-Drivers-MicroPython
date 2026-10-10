"""QMC5883P asynchronous magnetometer demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from qmc5883p_async import QMC5883PAsync

I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
QMC5883P_ADDR = 0x2C


async def main():
    await asyncio.sleep_ms(3000)
    i2c = None
    sensor = None
    try:
        i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        if QMC5883P_ADDR not in i2c.scan():
            raise RuntimeError('QMC5883P not found at 0x%02X' % QMC5883P_ADDR)
        sensor = QMC5883PAsync(i2c=i2c)
        await sensor.initialize_async()
        while True:
            print(await sensor.read_scaled_async())
            await asyncio.sleep_ms(300)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c is not None and hasattr(i2c, 'deinit'):
            i2c.deinit()


asyncio.run(main())