try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from lm75a_async import LM75AAsync
async def main():
    i2c = None; sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
        if 0x48 not in i2c.scan(): raise RuntimeError("LM75A not found at address 0x48")
        sensor = LM75AAsync(i2c, address=0x48, debug=True)
        await sensor.thyst_async(24.0)
        await sensor.tos_async(27.0)
        last_print_time = time.ticks_ms()
        while True:
            if time.ticks_diff(time.ticks_ms(), last_print_time) >= 2000:
                print("Temperature: {:.2f} C".format(await sensor.temp_async()))
                last_print_time = time.ticks_ms()
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None: await sensor.aclose()
        if i2c is not None:
            deinit=getattr(i2c,'deinit',None)
            if deinit is not None: deinit()
if __name__ == '__main__': asyncio.run(main())