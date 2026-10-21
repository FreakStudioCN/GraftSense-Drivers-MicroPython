# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : GP2Y0E03 asynchronous demonstration
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from gp2y0e03_async import GP2Y0E03Async

# ======================================== 全局变量 ============================================
I2C_ID = 0
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 100000
SENSOR_ADDR = 0x40
PRINT_INTERVAL = 500
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    i2c = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Testing GP2Y0E03 distance sensor driver")
        i2c = I2C(I2C_ID, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        if SENSOR_ADDR not in devices:
            raise RuntimeError("GP2Y0E03 not found at address 0x%02X" % SENSOR_ADDR)
        print("GP2Y0E03 found at address: 0x%02X" % SENSOR_ADDR)
        sensor = GP2Y0E03Async(i2c, address=SENSOR_ADDR)
        print("Shift: %d" % sensor._shift)
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
                raw = await sensor.read_async(raw=True)
                distance = await sensor.read_async()
                print("Raw: %d, Distance: %.2f cm" % (raw, distance))
                last_print_time = current_time
            await asyncio.sleep_ms(10)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())