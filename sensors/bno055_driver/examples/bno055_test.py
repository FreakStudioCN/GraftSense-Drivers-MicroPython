# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24 00:00
# @Author  : Peter Hinch
# @File    : bno055_test.py
# @Description : Manual BNO055 MicroPython test helpers
# @License : MIT

__version__ = "1.0.0"
__author__ = "Peter Hinch"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

import machine
import time
from bno055 import BNO055

# ======================================== 全局变量 ============================================

DEFAULT_I2C_ID = 0
DEFAULT_SDA_PIN = 16
DEFAULT_SCL_PIN = 17
DEFAULT_ADDRESS = 0x28
DEFAULT_INTERVAL = 1

# ======================================== 功能函数 ============================================


def create_i2c(i2c_id: object = DEFAULT_I2C_ID, sda_pin: object = DEFAULT_SDA_PIN, scl_pin: object = DEFAULT_SCL_PIN, soft: object = False) -> object:
    if not isinstance(i2c_id, int) or i2c_id < 0:
        raise ValueError("i2c_id must be a non-negative integer")
    if not isinstance(sda_pin, int) or not isinstance(scl_pin, int):
        raise ValueError("sda_pin and scl_pin must be integers")
    if not isinstance(soft, bool):
        raise ValueError("soft must be bool")
    if soft:
        return machine.SoftI2C(sda=machine.Pin(sda_pin), scl=machine.Pin(scl_pin), timeout=1000)
    return machine.I2C(i2c_id, sda=machine.Pin(sda_pin), scl=machine.Pin(scl_pin), freq=100000)


def print_sample(imu: object) -> None:
    if not hasattr(imu, "euler") or not hasattr(imu, "quaternion"):
        raise ValueError("imu must be a BNO055 instance")
    print("Calibration required: sys %d gyro %d accel %d mag %d" % tuple(imu.cal_status()))
    print("Temperature %d C" % imu.temperature())
    print("Mag       x %5.0f    y %5.0f     z %5.0f" % imu.mag())
    print("Gyro      x %5.0f    y %5.0f     z %5.0f" % imu.gyro())
    print("Accel     x %5.1f    y %5.1f     z %5.1f" % imu.accel())
    print("Lin acc.  x %5.1f    y %5.1f     z %5.1f" % imu.lin_acc())
    print("Gravity   x %5.1f    y %5.1f     z %5.1f" % imu.gravity())
    print("Heading     %4.0f roll %4.0f pitch %4.0f" % imu.euler())
    print("Quat      w %5.3f    x %5.3f     y %5.3f     z %5.3f" % imu.quaternion())


def run_test(sample_count: object = 10, interval: object = DEFAULT_INTERVAL, soft: object = False) -> None:
    if not isinstance(sample_count, int) or sample_count < 1:
        raise ValueError("sample_count must be a positive integer")
    if not isinstance(interval, (int, float)) or interval <= 0:
        raise ValueError("interval must be positive")
    if not isinstance(soft, bool):
        raise ValueError("soft must be bool")
    i2c = create_i2c(soft=soft)
    imu = BNO055(i2c, address=DEFAULT_ADDRESS)
    try:
        for _ in range(sample_count):
            print_sample(imu)
            time.sleep(interval)
    finally:
        imu.deinit()


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
