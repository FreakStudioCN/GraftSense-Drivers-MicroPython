# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 12:00
# @Author  : 李清水
# @File    : main.py
# @Description : Async DDS signal generator demo
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SPI
from dds_async import AD9833Async, MCP41010Async, DDSAsync

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================
async def main():
    await asyncio.sleep(3)
    print("FreakStudio: starting async driver demo")
    clk, mosi = Pin(18, Pin.OUT), Pin(19, Pin.OUT)
    ad9833_cs, mcp41010_cs = Pin(20, Pin.OUT), Pin(21, Pin.OUT)
    spi = SPI(0, baudrate=1000000, polarity=0, phase=1, sck=clk, mosi=mosi)
    ad9833 = AD9833Async(spi, ad9833_cs, clk, fmclk=25)
    mcp41010 = MCP41010Async(spi, mcp41010_cs, max_value=255)
    dds = DDSAsync(ad9833, mcp41010)
    try:
        await dds.initialize_async()
        await dds.set_frequency_async(5000, 0)
        await dds.set_phase_async(0, 0, rads=False)
        await dds.set_frequency_async(1300, 1)
        await dds.set_phase_async(180, 1, rads=False)
        await dds.select_freq_phase_async(0, 0)
        await dds.set_value_async(125)
        await dds.select_freq_phase_async(0, 0)
        await dds.set_mode_async("SIN")
    finally:
        await dds.aclose()
        spi.deinit()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
asyncio.run(main())
