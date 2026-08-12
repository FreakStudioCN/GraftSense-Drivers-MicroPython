# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/07/24
# @Author  : Sebastian Plamauer
# @File    : attitude.py
# @Description : Attitude angle helpers for BMX055 accelerometer and magnetometer data
# @License : MIT

__version__ = "1.0.0"
__author__ = "Sebastian Plamauer"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================
import math

# ======================================== 全局变量 ============================================
_RAD_TO_DEG = 180.0 / math.pi


# ======================================== 功能函数 ============================================
def angles(imu_data: tuple) -> tuple:
    if not isinstance(imu_data, tuple) or len(imu_data) != 3:
        raise ValueError("imu_data must be a 3-item tuple")
    x, y, z = imu_data
    roll = math.atan2(y, math.sqrt(x * x + z * z))
    pitch = math.atan2(-x, math.sqrt(y * y + z * z))
    return (roll * _RAD_TO_DEG, pitch * _RAD_TO_DEG)


def heading(mag_data: tuple) -> float:
    if not isinstance(mag_data, tuple) or len(mag_data) != 3:
        raise ValueError("mag_data must be a 3-item tuple")
    x, y, _z = mag_data
    value = math.atan2(y, x) * _RAD_TO_DEG
    if value < 0:
        value += 360.0
    return value


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================


# ========================================  主程序  ============================================
