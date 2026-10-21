try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from ip5306_async import IP5306Async

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
IP5306_I2C_ADDR = 0x75
PRINT_INTERVAL_MS = 2000


async def main():
    device = None
    await asyncio.sleep(3)
    print("FreakStudio: Testing IP5306 battery level driver...")
    try:
        i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus")
        if IP5306_I2C_ADDR not in devices:
            raise RuntimeError("IP5306 not found at expected address 0x%02X" % IP5306_I2C_ADDR)
        device = IP5306Async(i2c, address=IP5306_I2C_ADDR)
        print("IP5306 initial battery level: %d%%" % await device.level_async())
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                print("Battery level: %d%%" % await device.level_async())
                last_print_time = current_time
            await asyncio.sleep_ms(500)
    finally:
        if device is not None:
            await device.aclose()

if __name__ == '__main__':
    asyncio.run(main())
