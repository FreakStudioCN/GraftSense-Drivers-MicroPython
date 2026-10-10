try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from lm75_async import LM75Async
async def main():
    i2c = None; sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
        if 0x48 not in i2c.scan(): raise RuntimeError("LM75 not found at address 0x48")
        sensor = LM75Async(i2c, addr=0x48, debug=False)
        last_print_time = time.ticks_ms()
        while True:
            if time.ticks_diff(time.ticks_ms(), last_print_time) >= 2000:
                temp_c, point = await sensor.get_temp_async()
                msb, lsb = await sensor.get_output_async()
                print("Temperature: {}.{} C Raw: {:02X} {:02X}".format(temp_c, point, msb, lsb))
                last_print_time = time.ticks_ms()
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None: await sensor.aclose()
        if i2c is not None:
            deinit=getattr(i2c,'deinit',None)
            if deinit is not None: deinit()
if __name__ == '__main__': asyncio.run(main())