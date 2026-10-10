try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from sht35_async import SHT35Async

I2C_ID = 0
I2C_SCL_PIN = 17
I2C_SDA_PIN = 16
I2C_FREQ = 400000
DEVICE_ADDR = 0x44
PRINT_INTERVAL_MS = 2000


async def main():
    print("FreakStudio: Testing SHT35 temperature and humidity sensor driver")
    await asyncio.sleep(3)
    i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    print("I2C initialized: scl=Pin(%d), sda=Pin(%d), freq=%dHz" % (I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ))
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    if DEVICE_ADDR not in devices:
        raise RuntimeError("SHT35 not found at address 0x%02X" % DEVICE_ADDR)
    sensor = SHT35Async(i2c, addr=DEVICE_ADDR, debug=False)
    try:
        try:
            status = await sensor.read_status_async()
            print("Device verified at 0x%02X, status=0x%04X" % (DEVICE_ADDR, status))
        except RuntimeError as error:
            print("WARNING: Status read failed: %s" % str(error))
        while True:
            temperature, humidity = await sensor.measure_async()
            print("Temperature: %.2f C, Humidity: %.2f %%RH" % (temperature, humidity))
            await asyncio.sleep_ms(PRINT_INTERVAL_MS)
    finally:
        await sensor.aclose()


if __name__ == "__main__":
    asyncio.run(main())
