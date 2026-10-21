# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:00
# @Author  : 缪贵成
# @File    : main.py
# @Description : PCF8574 asynchronous five-way key demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from pcf8574keys_async import PCF8574Async, PCF8574KeysAsync, KEYS_MAP

# ======================================== 全局变量 ============================================
I2C_ID = 0
SCL_PIN = 5
SDA_PIN = 4

# ======================================== 功能函数 ============================================
async def main() -> None:
    print("FreakStudio: starting async driver demo")
    await asyncio.sleep_ms(3000)
    i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
    addresses = i2c.scan()
    address = None
    for device in addresses:
        if 0x20 <= device <= 0x27:
            address = device
            break
    if address is None:
        raise RuntimeError("PCF8574 not found on I2C bus")
    pcf = PCF8574Async(i2c, address)
    keys = PCF8574KeysAsync(pcf, KEYS_MAP)
    await keys.start()
    try:
        while True:
            print(keys.read_all())
            if keys.read_key("SW1"):
                await keys.led_on_async()
            if keys.read_key("SW2"):
                await keys.led_off_async()
            await asyncio.sleep_ms(100)
    finally:
        await keys.aclose()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
asyncio.run(main())
