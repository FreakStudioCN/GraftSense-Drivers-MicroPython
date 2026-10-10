try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C
from pca9546adr_async import PCA9546ADRAsync


async def main():
    pca = None
    await asyncio.sleep(3)
    print("FreakStudio: Testing PCA9546ADR4 I2C Multiplexer Modules")
    try:
        i2c = I2C(1, scl=Pin(2), sda=Pin(3))
        pca = PCA9546ADRAsync(i2c)
        while True:
            await pca.disable_all_async()
            await pca.select_channel_async(0)
            print("0 address", i2c.scan())
            await asyncio.sleep(4)
            await pca.disable_all_async()
            await pca.select_channel_async(1)
            print("1 address", i2c.scan())
            await asyncio.sleep(4)
    finally:
        if pca is not None:
            await pca.aclose()

if __name__ == '__main__':
    asyncio.run(main())
