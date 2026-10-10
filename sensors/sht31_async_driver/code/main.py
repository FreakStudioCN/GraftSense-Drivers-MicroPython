try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin
from sht31_async import SHT31Async

SHT31_ADDR = 0x44
_PRINT_INTERVAL_MS = 2000


async def main():
    sensor = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Testing SHT31 driver module")
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    devices = i2c.scan()
    print("Devices found: %s" % [hex(device) for device in devices])
    if not devices:
        raise RuntimeError("No I2C device found on bus")
    if SHT31_ADDR not in devices:
        raise RuntimeError("SHT31 not found at expected address 0x%02X" % SHT31_ADDR)
    try:
        sensor = SHT31Async(i2c, addr=SHT31_ADDR, debug=False)
        last_print_time = time.ticks_ms()
        print("SHT31 sensor initialized successfully")
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= _PRINT_INTERVAL_MS:
                temperature, humidity = await sensor.get_temp_humi_async()
                print("T=%.2f C  RH=%.2f %%" % (temperature, humidity))
                last_print_time = current_time
            await asyncio.sleep_ms(100)
    finally:
        if sensor is not None:
            await sensor.aclose()
        print("Program exited")


asyncio.run(main())