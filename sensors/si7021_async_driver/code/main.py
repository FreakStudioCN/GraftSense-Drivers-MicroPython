try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import Pin, I2C
from si7021_async import Si7021Async, CRCError

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
SI7021_ADDR = 0x40
PRINT_INTERVAL_MS = 2000


async def main():
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        if SI7021_ADDR not in i2c.scan():
            raise RuntimeError("Device not found at expected address 0x%02X" % SI7021_ADDR)
        sensor = Si7021Async(i2c, address=SI7021_ADDR, debug=False)
        await sensor.initialize_async()
        print("Device found: %s (serial: %d)" % (sensor.identifier, sensor.serial))
        last_print_time = time.ticks_ms()
        while True:
            now = time.ticks_ms()
            if time.ticks_diff(now, last_print_time) >= PRINT_INTERVAL_MS:
                temperature = await sensor.temperature_async()
                humidity = await sensor.relative_humidity_async()
                print("Temperature: %.2f C | Humidity: %.2f %%RH" % (temperature, humidity))
                last_print_time = now
            await asyncio.sleep_ms(100)
    except CRCError as error:
        print("CRC check error: %s" % error)
    finally:
        if sensor is not None:
            await sensor.aclose()


if __name__ == '__main__':
    asyncio.run(main())