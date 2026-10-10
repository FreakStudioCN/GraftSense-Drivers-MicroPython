# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : GraftSense Async Conversion
# @File    : main.py
# @Description : APA102 asynchronous demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SPI
from apa102_async import DotStarAsync, BGR

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
async def main():
    await asyncio.sleep_ms(3000)
    spi = SPI(1, baudrate=4000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23))
    device = DotStarAsync(spi, 8, brightness=0.2, pixel_order=BGR)
    try:
        await device.fill_async((255, 0, 0)); await device.show_async()
        await device.color_wipe_async((0, 255, 0), 50)
    finally: await device.aclose()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
asyncio.run(main())
