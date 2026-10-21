# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/08/21 16:44
# @Author  : December
# @File    : main.py
# @Description : MHT04-IIC 温湿度传感器异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from mht04 import MHT04Error
from mht04_async import MHT04Async

# ======================================== 全局变量 ============================================
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQUENCY = 100000
DEVICE_ADDRESS = 0x44
PRINT_INTERVAL_MS = 1000

# ======================================== 功能函数 ============================================
def deinit_if_present(resource):
    deinit = getattr(resource, "deinit", None)
    if deinit is not None:
        deinit()

async def scan_i2c(i2c):
    devices = i2c.scan()
    if not devices:
        raise RuntimeError("No I2C device found")
    print("I2C devices: %s" % ["0x%02X" % address for address in devices])
    if DEVICE_ADDRESS not in devices:
        raise RuntimeError("Device not found at expected address")
    await asyncio.sleep_ms(0)
    return DEVICE_ADDRESS

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
async def main():
    """Keep source address verification and conversion cadence with async calls."""
    i2c = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: Using Mysentech MHT04-IIC sensor ...")
        i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQUENCY)
        driver_address = await scan_i2c(i2c)
        sensor = MHT04Async(i2c=i2c, address=driver_address)
        configuration = await sensor.refresh_configuration_async()
        print("MHT04 configuration: %s" % configuration)
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
                temperature, humidity = await sensor.read_async()
                print("Temperature: %.2f C, Humidity: %.2f %%RH" % (temperature, humidity))
                last_print_time = current_time
            await asyncio.sleep_ms(10)
    except MHT04Error as error:
        print("MHT04 driver error: %s" % error)
    finally:
        if sensor is not None:
            await sensor.aclose()
        deinit_if_present(i2c)

# ======================================== 初始化入口 =============================================
if __name__ == "__main__":
    asyncio.run(main())