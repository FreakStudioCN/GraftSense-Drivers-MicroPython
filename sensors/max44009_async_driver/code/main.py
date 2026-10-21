# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : main.py
# @Description : MAX44009 asynchronous ambient-light demonstration
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from max44009_async import MAX44009Async

# ======================================== globals =============================================

I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000
MAX44009_ADDR_LIST = (0x4A, 0x4B)
I2C_MUX_ADDR = 0x70
I2C_MUX_CHANNELS = 8
READ_INTERVAL = 1

# ======================================== functions ===========================================

def select_mux_channel(i2c, channel):
    if channel < 0 or channel >= I2C_MUX_CHANNELS:
        raise ValueError("Mux channel out of range")
    i2c.writeto(I2C_MUX_ADDR, bytes([1 << channel]))

async def find_sensor_with_mux(i2c):
    devices = i2c.scan()
    for address in MAX44009_ADDR_LIST:
        if address in devices:
            return address, None
    if I2C_MUX_ADDR not in devices:
        raise RuntimeError("MAX44009 not found")
    for channel in range(I2C_MUX_CHANNELS):
        select_mux_channel(i2c, channel)
        await asyncio.sleep_ms(10)
        devices = i2c.scan()
        for address in MAX44009_ADDR_LIST:
            if address in devices:
                return address, channel
    i2c.writeto(I2C_MUX_ADDR, b"\x00")
    raise RuntimeError("MAX44009 not found")

# ======================================== classes =============================================

# ======================================== init ================================================

# ======================================== main ================================================

async def main():
    """Preserve direct/mux discovery and periodic source measurements."""
    i2c = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        sensor_address, mux_channel = await find_sensor_with_mux(i2c)
        sensor = MAX44009Async(i2c, address=sensor_address)
        await sensor.set_continuous_async(1)
        await sensor.set_manual_async(0)
        await sensor.set_current_division_ratio_async(0)
        await sensor.set_integration_time_async(3)
        print("MAX44009 address: 0x%02X mux: %s" % (sensor_address, mux_channel))
        while True:
            lux = await sensor.read_lux_async()
            lux_fast = await sensor.read_lux_fast_async()
            status = await sensor.read_int_status_async()
            print("Lux: %.2f lx Fast: %.2f lx Interrupt: %d" % (lux, lux_fast, status))
            await asyncio.sleep(READ_INTERVAL)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

if __name__ == '__main__':
    asyncio.run(main())