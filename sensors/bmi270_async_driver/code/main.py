try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/19
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : 测试 BMI270 六轴IMU驱动类的代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
from machine import I2C, Pin
import time
from bmi270 import BMI270

# ======================================== 全局变量 ============================================
# BMI270 默认 I2C 地址
BMI270_I2C_ADDR = 0x68
# BMI270 WHO_AM_I 期望值
BMI270_CHIP_ID = 0x24
# BMI270 WHO_AM_I 寄存器地址
BMI270_WHO_AM_I_REG = 0x00
# 打印间隔（ms）
PRINT_INTERVAL = 2000
# 上次打印时间戳
last_print_time = 0
bmi270 = None


# ======================================== 功能函数 ============================================
def print_error_codes():
    """
    打印错误代码（调试功能，默认注释调用，可 REPL 手动调用）
    Print error codes (debug function, commented by default, can be called from REPL).
    """
    bmi270.error_code()


def switch_gyro_range():
    """
    切换陀螺仪量程到 ±1000 dps（模式切换，默认注释调用，可 REPL 手动触发）
    Switch gyro range to +/-1000 dps (mode switch, commented by default, can be triggered from REPL).
    """
    bmi270.gyro_range = bmi270.GYRO_RANGE_1000
    print("Gyro range switched to GYRO_RANGE_1000")


def switch_accel_range():
    """
    切换加速度量程到 ±8g（模式切换，默认注释调用，可 REPL 手动触发）
    Switch acceleration range to +/-8g (mode switch, commented by default, can be triggered from REPL).
    """
    bmi270.acceleration_range = bmi270.ACCEL_RANGE_8G
    print("Accel range switched to ACCEL_RANGE_8G")


# ======================================== 自定义类 ============================================
# 无自定义类，直接使用 bmi270.BMI270

# ======================================== 初始化配置 ==========================================

async def main():
    global bmi270
    i2c = None
    bmi270 = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Testing BMI270 6-axis IMU driver")
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        devices = i2c.scan()
        if not devices:
            raise RuntimeError("No I2C device found on bus")
        if BMI270_I2C_ADDR not in devices:
            raise RuntimeError("BMI270 not found at expected address 0x%02X" % BMI270_I2C_ADDR)
        chip_id = i2c.readfrom_mem(BMI270_I2C_ADDR, BMI270_WHO_AM_I_REG, 1)[0]
        if chip_id != BMI270_CHIP_ID:
            raise RuntimeError("Unexpected BMI270 chip ID: expected 0x%02X, got 0x%02X" % (BMI270_CHIP_ID, chip_id))
        bmi270 = BMI270(i2c, address=BMI270_I2C_ADDR, debug=False)
        await bmi270.initialize_async()
        print("BMI270 initialized successfully")
        last_print_time = time.ticks_ms()
        while True:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL:
                acc_x, acc_y, acc_z = bmi270.acceleration
                gyro_x, gyro_y, gyro_z = bmi270.gyro
                print("Accel (m/s^2): x=%.3f, y=%.3f, z=%.3f" % (acc_x, acc_y, acc_z))
                print("Gyro (dps): x=%.3f, y=%.3f, z=%.3f" % (gyro_x, gyro_y, gyro_z))
                print("Range: accel=%s, gyro=%s" % (bmi270.acceleration_range, bmi270.gyro_range))
                last_print_time = current_time
            await asyncio.sleep_ms(100)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        if bmi270 is not None:
            await bmi270.aclose()
        if i2c is not None:
            close_bus = getattr(i2c, "deinit", None)
            if close_bus is not None:
                close_bus()
        bmi270 = None
        print("Program exited")
# ======================================== 主程序 ==============================================
asyncio.run(main())
