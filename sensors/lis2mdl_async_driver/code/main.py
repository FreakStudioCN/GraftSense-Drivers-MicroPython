try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from micropython_lis2mdl.lis2mdl import RATE_100_HZ, data_rate_values
from micropython_lis2mdl.lis2mdl_async import LIS2MDLAsync
async def main():
    i2c_bus = None; sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
        if 0x1E not in i2c_bus.scan(): raise RuntimeError("LIS2MDL not found")
        sensor = LIS2MDLAsync(i2c_bus)
        await sensor.set_data_rate_async(RATE_100_HZ)
        while True:
            for data_rate in data_rate_values:
                print("Current Data rate setting: {}".format(sensor.data_rate))
                for _ in range(10):
                    x, y, z = await sensor.magnetic_async()
                    print("X:{:.2f}, Y:{:.2f}, Z:{:.2f} uT".format(x, y, z))
                    await asyncio.sleep_ms(500)
                await sensor.set_data_rate_async(data_rate)
    finally:
        if sensor is not None: await sensor.aclose()
        if i2c_bus is not None:
            deinit=getattr(i2c_bus,'deinit',None)
            if deinit is not None: deinit()
if __name__ == '__main__': asyncio.run(main())