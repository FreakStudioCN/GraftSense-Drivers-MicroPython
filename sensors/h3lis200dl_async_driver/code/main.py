# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : H3LIS200DL asynchronous demonstration
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, I2C
from h3lis200dl_async import H3LIS200DLAsync

# ======================================== 全局变量 ============================================
TARGET_H3LIS200DL_ADDRS = (0x18, 0x19)
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    i2c_bus = None
    sensor = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: H3LIS200DL accelerometer initialization")
        i2c_bus = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        devices_list = i2c_bus.scan()
        if not devices_list:
            raise SystemExit("I2C scan found no devices, program exited")
        for device in devices_list:
            if device in TARGET_H3LIS200DL_ADDRS:
                sensor = H3LIS200DLAsync(i2c_bus, address=device)
                print("Sensor initialization successful at", hex(device))
                break
        if sensor is None:
            raise RuntimeError("No target sensor device found in I2C bus")
        while True:
            accx, accy, accz = await sensor.get_acceleration_async()
            print("x:{:.2f}g, y:{:.2f}g, z:{:.2f}g".format(accx, accy, accz))
            await asyncio.sleep_ms(500)
    finally:
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())