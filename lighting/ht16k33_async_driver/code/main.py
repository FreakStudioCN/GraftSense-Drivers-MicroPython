# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:20
# @Author  : mcauser
# @File    : main.py
# @Description : HT16K33 asynchronous demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from ht16k33_async import Seg7x4Async

# ======================================== 全局变量 ============================================
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_SENSOR_ADDR = 0x70

# ======================================== 功能函数 ============================================
async def _show_text_async(seg7: Seg7x4Async, value: str, hold_ms: int) -> None:
    seg7.fill(False)
    seg7.text(value)
    await seg7.show_async()
    await asyncio.sleep_ms(hold_ms)

async def main() -> None:
    print("FreakStudio: starting async driver demo")
    await asyncio.sleep_ms(3000)
    i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    if TARGET_SENSOR_ADDR not in i2c_bus.scan():
        raise RuntimeError("HT16K33 not found on I2C bus")
    seg7 = Seg7x4Async(i2c=i2c_bus, address=TARGET_SENSOR_ADDR)
    try:
        await _show_text_async(seg7, "1234", 2000)
        await _show_text_async(seg7, "8.888", 2000)
        seg7.fill(False)
        seg7.hex(0xFAB)
        await seg7.show_async()
        await asyncio.sleep_ms(2000)
        seg7.fill(False)
        seg7.put("9", 0)
        seg7.put("8", 1)
        seg7.put("7", 2)
        seg7.put("6", 3)
        await seg7.show_async()
        await asyncio.sleep_ms(2000)
        for value in range(0, 16, 3):
            await seg7.brightness_async(value)
            await asyncio.sleep_ms(500)
    finally:
        seg7.fill(False)
        await seg7.show_async()
        await seg7.aclose()

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
asyncio.run(main())
