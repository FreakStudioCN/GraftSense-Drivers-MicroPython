try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from _gs_isl29125_micropython_isl29125.isl29125 import RED_GREEN_BLUE, LUX_10K, RES_16BITS
from _gs_isl29125_micropython_isl29125.isl29125_async import ISL29125Async
async def main():
    i2c_bus = None; sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
        if 0x44 not in i2c_bus.scan(): raise RuntimeError("ISL29125 not found")
        sensor = ISL29125Async(i2c_bus, address=0x44)
        await sensor.configure_async(RED_GREEN_BLUE, LUX_10K, RES_16BITS)
        while True:
            red, green, blue = await sensor.colors_async()
            print("R:{} G:{} B:{}".format(red, green, blue))
            await asyncio.sleep_ms(500)
    finally:
        if sensor is not None: await sensor.aclose()
        if i2c_bus is not None:
            deinit=getattr(i2c_bus,'deinit',None)
            if deinit is not None: deinit()
if __name__ == '__main__': asyncio.run(main())