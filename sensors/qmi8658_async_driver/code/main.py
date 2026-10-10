"""QMI8658 asynchronous six-axis IMU demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from qmi8658_async import QMI8658Async

I2C_ID = 0
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
I2C_FREQ = 400000
QMI8658_ADDR = 0x6B


async def main():
    await asyncio.sleep_ms(3000)
    i2c = None
    sensor = None
    try:
        i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
        if QMI8658_ADDR not in i2c.scan():
            raise RuntimeError('QMI8658 not found at 0x%02X' % QMI8658_ADDR)
        sensor = QMI8658Async(i2c, address=QMI8658_ADDR)
        await sensor.initialize_async()
        print('WHO_AM_I: 0x%02X' % await sensor.who_am_i_async())
        print('Revision:', await sensor.revision_async())
        while True:
            print('Raw:', await sensor.read_raw_async())
            print('XYZ:', await sensor.read_xyz_async())
            await asyncio.sleep_ms(1000)
    finally:
        if sensor is not None:
            await sensor.deinit_async()
        if i2c is not None and hasattr(i2c, 'deinit'):
            i2c.deinit()


asyncio.run(main())