# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @File    : main.py
# @Description : LCD1602 I2C asynchronous example

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from LCD_I2C_async import LCDAsync

# ======================================== 全局变量 ============================================
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_LCD_ADDRS = (0x27, 0x3E)

# ======================================== 功能函数 ============================================
def find_lcd_address(i2c_bus):
    """Return the first supported LCD1602 address discovered on the bus."""
    for address in i2c_bus.scan():
        if address in TARGET_LCD_ADDRS:
            return address
    raise RuntimeError("No LCD1602 device found at 0x27 or 0x3E")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
async def main():
    """Preserve the source display sequence with cooperative display delays."""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Control LCD1602 via I2C")
    i2c_bus = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    address = find_lcd_address(i2c_bus)
    print("I2C hexadecimal address: %s" % hex(address))
    lcd = LCDAsync(i2c_bus, address)
    try:
        await lcd.start()
        await lcd.set_cursor_async(0, 0)
        await lcd.write_async("Hello World")
        await asyncio.sleep_ms(1000)
        await lcd.off_async()
        await asyncio.sleep_ms(1000)
        await lcd.on_async()
        await asyncio.sleep_ms(1000)
        await lcd.on_async(cursor=False, blink=True)
        await asyncio.sleep_ms(1000)
        await lcd.on_async(cursor=True, blink=False)
        await asyncio.sleep_ms(1000)
        await lcd.on_async(cursor=True, blink=True)
        await asyncio.sleep_ms(1500)
        await lcd.clear_async()
    finally:
        await lcd.aclose()

# ======================================== 主程序 ==============================================
asyncio.run(main())
