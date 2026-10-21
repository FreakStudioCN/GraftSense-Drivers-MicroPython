import time

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, I2C
import micropython_icp10111.icp10111 as icp10111
from icp10111_async import ICP10111Async


async def main():
    icp = None
    i2c = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Read ICP10111 pressure and temperature data")
        i2c = I2C(0, sda=Pin(4), scl=Pin(5))
        icp = ICP10111Async(i2c)
        icp.operation_mode = icp10111.NORMAL
        while True:
            for operation_mode in icp10111.operation_mode_values:
                print("Current Operation mode setting: ", icp.operation_mode)
                for _ in range(10):
                    press, temp = await icp.measurements_async()
                    print(f"Pressure {press:.2f}KPa")
                    print(f"Temperature {temp:.2f}°C")
                    print()
                    await asyncio.sleep_ms(500)
                icp.operation_mode = operation_mode
    finally:
        if icp is not None:
            await icp.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()


asyncio.run(main())