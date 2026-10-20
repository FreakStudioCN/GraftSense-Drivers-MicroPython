# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 李清水
# @File    : main.py
# @Description : PCA9685 总线直流电机异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from bus_dc_motor_async import BusDCMotorAsync
from _gs_bus_dc_motor_pca9685 import PCA9685

# ======================================== 全局变量 ============================================
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400000
MOTOR_NUMBER = 4
MOTOR_SPEED = 4000
RUN_TIME_MS = 10000

# ======================================== 功能函数 ============================================
async def main() -> None:
    """扫描 PCA9685 后运行来源示例中的四号电机。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Using PCA9685 to control dc motor and step motor")
    i2c = None
    motor = None
    try:
        i2c = I2C(id=I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
        devices = i2c.scan()
        address = next((device for device in devices if 0x40 <= device <= 0x4F), None)
        if address is None:
            print("No PCA9685 I2C device found")
            return
        print("PCA9685 I2C hexadecimal address:", hex(address))
        motor = BusDCMotorAsync(PCA9685(i2c, address), 4)
        print("Motor 4 started: Speed = 4000, Direction = 0")
        await motor.set_motor_speed_async(MOTOR_NUMBER, MOTOR_SPEED, 0)
        await asyncio.sleep_ms(RUN_TIME_MS)
    finally:
        try:
            if motor is not None:
                await motor.stop_motor_async(MOTOR_NUMBER)
                await motor.aclose()
                print("Motor 4 stopped successfully")
        finally:
            if i2c is not None:
                i2c.deinit()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())
