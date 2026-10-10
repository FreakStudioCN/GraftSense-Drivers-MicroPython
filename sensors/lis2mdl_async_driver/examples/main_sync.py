# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : LIS2MDL磁力传感器数据读取程序，支持I2C设备自动扫描和初始化
# @License : MIT
__version__ = "0.1.0"
__author__ = "Jose D. Montoya"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"


# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from micropython_lis2mdl import lis2mdl


# ======================================== 全局变量 ============================================

# 目标传感器地址列表
TARGET_SENSOR_ADDRS = [0x1E]


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

# I2C总线初始化，使用软件I2C方式
i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器
sensor = None  # 初始化传感器对象占位符
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = lis2mdl.LIS2MDL(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# 设置传感器数据输出速率为100Hz
sensor.data_rate = lis2mdl.RATE_100_HZ


# ========================================  主程序  ============================================

# 主循环：遍历所有数据速率模式，连续读取磁场数据
while True:
    for data_rate in lis2mdl.data_rate_values:
        print("Current Data rate setting: ", sensor.data_rate)
        for _ in range(10):
            mag_x, mag_y, mag_z = sensor.magnetic
            print(f"X:{mag_x:.2f}, Y:{mag_y:.2f}, Z:{mag_z:.2f} uT")
            print()
            time.sleep(0.5)
        sensor.data_rate = data_rate
