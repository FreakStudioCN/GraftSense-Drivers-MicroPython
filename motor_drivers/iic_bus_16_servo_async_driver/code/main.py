# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : main.py
# @Description : PCA9685 十六路总线舵机异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from bus_servo import BusPWMServoController
from bus_servo_async import BusPWMServoControllerAsync
from pca9685 import PCA9685

# ======================================== 全局变量 ============================================
I2C_ID = 0
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400000
SERVO_FREQ = 50
ROTATION_DELAY_MS = 20000

# ======================================== 功能函数 ============================================
async def main() -> None:
    """执行来源示例的 180 度及连续旋转舵机动作。"""
    await asyncio.sleep_ms(3000)
    i2c = None
    servos = None
    try:
        i2c = I2C(id=I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
        address = next((value for value in i2c.scan() if 0x40 <= value <= 0x4F), None)
        if address is None:
            raise RuntimeError("PCA9685 not found")
        controller = BusPWMServoController(PCA9685(i2c, address=address), freq=SERVO_FREQ)
        servos = BusPWMServoControllerAsync(controller)
        for channel in range(4):
            await servos.attach_servo_async(channel, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
            await servos.set_angle_async(channel, 0)
        for channel in (4, 5):
            await servos.attach_servo_async(channel, BusPWMServoController.SERVO_360, min_us=1000, max_us=2000, neutral_us=1500)
        for channel in range(4):
            await servos.set_angle_async(channel, 90, speed_deg_per_s=120)
            await servos.set_angle_async(channel, 180, speed_deg_per_s=180)
        await servos.stop_async(0)
        await servos.set_speed_async(4, 0.6)
        await servos.set_speed_async(5, 0.6)
        await asyncio.sleep_ms(ROTATION_DELAY_MS)
        await servos.set_speed_async(4, -0.6)
        await servos.set_speed_async(5, -0.6)
        await asyncio.sleep_ms(ROTATION_DELAY_MS)
    finally:
        try:
            if servos is not None:
                for channel in range(6):
                    await servos.detach_servo_async(channel)
                await servos.aclose()
        finally:
            if i2c is not None:
                i2c.deinit()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())
