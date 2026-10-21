# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : ADT7410 asynchronous temperature example
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C
from adt7410_async import ADT7410Async

I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_ADDR = 0x48
WHOAMI_REG = 0x0B
EXPECTED_DEVICE_ID = 0xCB
PRINT_INTERVAL_MS = 2000


async def main():
    adt = None
    try:
        # Preserve the source demo's power-up, scan, and ID-verification order.
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
        devices = i2c.scan()
        if I2C_ADDR not in devices:
            raise RuntimeError("Device not found at 0x%02X" % I2C_ADDR)
        whoami = i2c.readfrom_mem(I2C_ADDR, WHOAMI_REG, 1)[0]
        if whoami != EXPECTED_DEVICE_ID:
            raise RuntimeError("Unexpected ADT7410 ID: 0x%02X" % whoami)
        adt = ADT7410Async(i2c, address=I2C_ADDR)
        print("ADT7410 initialized; temperature: %.4f C" % await adt.temperature_async())
        while True:
            await asyncio.sleep_ms(PRINT_INTERVAL_MS)
            print("Temperature: %.4f C" % await adt.temperature_async())
    finally:
        if adt is not None:
            await adt.aclose()


if __name__ == "__main__":
    asyncio.run(main())