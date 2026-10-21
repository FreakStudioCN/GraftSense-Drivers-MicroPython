try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from _gs_lis3mdl_micropython_lis3mdl.lis3mdl_async import LIS3MDLAsync
async def main():
    i2c_bus = None; sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
        if not any(address in (0x1C, 0x1E) for address in i2c_bus.scan()): raise RuntimeError("LIS3MDL not found")
        sensor = LIS3MDLAsync(i2c_bus)
        while True:
            x, y, z = await sensor.magnetic_async()
            print("X:{:.2f}, Y:{:.2f}, Z:{:.2f} uT".format(x,y,z))
            await asyncio.sleep_ms(500)
    finally:
        if sensor is not None: await sensor.aclose()
        if i2c_bus is not None:
            deinit=getattr(i2c_bus,'deinit',None)
            if deinit is not None: deinit()
if __name__ == '__main__': asyncio.run(main())