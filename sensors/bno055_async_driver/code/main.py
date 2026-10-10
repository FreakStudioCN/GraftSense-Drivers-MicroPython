# ======================================== 导入相关模块 =========================================
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : Peter Hinch, async adaptation by GraftSense
# @File    : main.py
# @Description : Async BNO055 demonstration
# @License : MIT

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import machine
from bno055_async import BNO055Async

I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 100000
BNO055_ADDR = 0x29
USE_SOFT_I2C = False


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
async def main():
    i2c = None
    sensor = None
    print("FreakStudio: starting async driver demo")
    try:
        if USE_SOFT_I2C:
            i2c = machine.SoftI2C(sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), timeout=1000)
        else:
            i2c = machine.I2C(I2C_ID, sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=I2C_FREQ)
        sensor = BNO055Async(i2c, address=BNO055_ADDR, crystal=True)
        await sensor.start()
        print("BNO055 initialized successfully")
        print("Current mode: %d" % await sensor.mode_async())
        print("Crystal: %s" % ("External" if await sensor.external_crystal_async() else "Internal"))
        while True:
            cal = await sensor.cal_status_async()
            print("Calibration S:%d G:%d A:%d M:%d" % cal)
            print("Temperature: %d C" % await sensor.temperature_async())
            print("Euler: %.3f, %.3f, %.3f" % await sensor.euler_async())
            print("Quaternion: %.3f, %.3f, %.3f, %.3f" % await sensor.quaternion_async())
            print("Accel: %.3f, %.3f, %.3f" % await sensor.accel_async())
            print("Gyro: %.3f, %.3f, %.3f" % await sensor.gyro_async())
            print("Mag: %.3f, %.3f, %.3f" % await sensor.mag_async())
            print("Linear accel: %.3f, %.3f, %.3f" % await sensor.lin_acc_async())
            print("Gravity: %.3f, %.3f, %.3f" % await sensor.gravity_async())
            await asyncio.sleep_ms(2000)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c is not None:
            close_bus = getattr(i2c, "deinit", None)
            if close_bus is not None:
                close_bus()
asyncio.run(main())
