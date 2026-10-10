# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : GraftSense
# @File    : main.py
# @Description : MLX90393 异步磁场测量示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from mlx90393_async import MLX90393Async

# ======================================== 全局变量 ============================================
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
TARGET_SENSOR_ADDRS = (0x0C,)
MEAS_DELAY_MS = 1000

# ======================================== 功能函数 ============================================
def deinit_if_present(resource):
    deinit = getattr(resource, "deinit", None)
    if deinit is not None:
        deinit()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
async def main():
    i2c_bus = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: MLX90393 magnetometer test starting ...")
        i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN))
        devices_list = i2c_bus.scan()
        print("I2C scan result: %s" % [hex(device) for device in devices_list])
        target = next((device for device in devices_list if device in TARGET_SENSOR_ADDRS), None)
        if target is None:
            raise RuntimeError("Target sensor not found on I2C bus")
        sensor = MLX90393Async(i2c=i2c_bus, address=target)
        while True:
            magx, magy, magz = await sensor.read_magnetic_async()
            print("X: %.2f uT | Y: %.2f uT | Z: %.2f uT" % (magx, magy, magz))
            await asyncio.sleep_ms(MEAS_DELAY_MS)
    finally:
        if sensor is not None:
            await sensor.aclose()
        deinit_if_present(i2c_bus)

# ======================================== 初始化入口 =============================================
if __name__ == "__main__":
    asyncio.run(main())