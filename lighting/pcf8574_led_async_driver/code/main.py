# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:10
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : PCF8574 LED bar asynchronous demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from pcf8574_led_async import PCF8574Async, LEDBarAsync

# ======================================== 全局变量 ============================================
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5

# ======================================== 功能函数 ============================================
async def main() -> None:
    print("FreakStudio: starting async driver demo")
    await asyncio.sleep_ms(3000)
    i2c = I2C(id=I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=100000)
    addresses = i2c.scan()
    address = next((item for item in addresses if 0x20 <= item <= 0x27), None)
    if address is None:
        raise RuntimeError("PCF8574 not found on I2C bus")
    pcf = PCF8574Async(i2c, address=address)
    ledbar = LEDBarAsync(pcf)
    try:
        await ledbar.set_led_async(2, True)
        await asyncio.sleep_ms(1000)
        await ledbar.set_led_async(2, False)
        await asyncio.sleep_ms(1000)
        await ledbar.set_all_async(0b00001111)
        await asyncio.sleep_ms(1000)
        await ledbar.display_level_async(6)
        await asyncio.sleep_ms(1000)
        for index in range(8):
            await ledbar.set_all_async(1 << index)
            await asyncio.sleep_ms(200)
    finally:
        await ledbar.clear_async()
        ledbar.deinit()

# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
asyncio.run(main())
