# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : FreakStudio
# @File    : main.py
# @Description : CC1101 sub-GHz SPI 收发器异步示例
# @License : GPL-3.0

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, SPI
from cc1101_async import CC1101Async as CC1101

# ======================================== 全局变量 ============================================
SPI_CHANNEL = 1
SCK_PIN = 18
MOSI_PIN = 23
MISO_PIN = 19
CS_PIN = 5
GDO0_PIN = 4
SPI_BAUDRATE = 4000000
TEST_FREQ_HZ = 433920000

# ======================================== 功能函数 ============================================
async def main() -> None:
    """验证 CC1101、设置来源示例的频率并保持设备空闲。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Testing CC1101 sub-GHz SPI transceiver driver...")
    cs_pin = Pin(CS_PIN, Pin.OUT)
    cs_pin.value(1)
    spi = SPI(SPI_CHANNEL, baudrate=SPI_BAUDRATE, polarity=0, phase=0, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
    device = CC1101(spi, cs_pin, gdo0=Pin(GDO0_PIN, Pin.IN), debug=True)
    try:
        await device.initialize_async()
        part, version = await device.verify_async()
        print("CC1101 part=0x%02X version=0x%02X" % (part, version))
        await device.set_frequency_async(TEST_FREQ_HZ)
        await device.idle_async()
        while True:
            await asyncio.sleep_ms(1000)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        await device.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())