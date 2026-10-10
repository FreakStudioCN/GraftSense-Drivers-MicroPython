# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Andre Peeters
# @File    : main.py
# @Description : MAX17048 asynchronous demonstration
# @License : MIT

# ======================================== imports =============================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import Pin, I2C
from max17048_async import MAX17048Async

# ======================================== globals =============================================

MAX17048_ADDR = 0x36
PRINT_INTERVAL = 2000

# ======================================== functions ===========================================


async def reset_device(device):
    return await device.reset_async()

async def quick_start_device(device):
    return await device.quickStart_async()

async def clear_alert(device):
    return await device.clearAlert_async()

async def set_alert_threshold(device, threshold=20):
    return await device.setAlertThreshold_async(threshold)
# ======================================== classes =============================================

# ======================================== init ================================================

# ======================================== main ================================================

async def main():
    """Preserve source discovery, version read and periodic gauge reads."""
    i2c = None
    device = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Testing MAX17048 LiPo fuel gauge driver...")
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
        if MAX17048_ADDR not in i2c.scan():
            raise RuntimeError("Device not found at expected address 0x%02X" % MAX17048_ADDR)
        device = MAX17048Async(i2c)
        print("MAX17048 version register: 0x%04X" % (await device.getVersion_async()))
        last_print_time = time.ticks_ms()
        while True:
            now = time.ticks_ms()
            if time.ticks_diff(now, last_print_time) >= PRINT_INTERVAL:
                voltage = await device.getVCell_async()
                soc = await device.getSoc_async()
                alert = await device.inAlert_async()
                print("Voltage: %.3f V | SOC: %.2f %% | Alert: %s" % (voltage, soc, alert))
                last_print_time = now
            await asyncio.sleep_ms(100)
    finally:
        if device is not None:
            await device.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

if __name__ == '__main__':
    asyncio.run(main())