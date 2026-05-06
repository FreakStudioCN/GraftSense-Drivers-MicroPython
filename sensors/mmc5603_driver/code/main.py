# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/15 下午3:30
# @Author  : hogeiha
# @File    : main.py
# @Description : MMC5603磁力计数据读取

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, SoftI2C
from micropython_mmc5603 import mmc5603

# ======================================== 全局变量 ============================================

# 目标传感器地址列表（MMC5603默认地址0x30）
TARGET_SENSOR_ADDRS = [0x30]

# I2C总线引脚与频率配置
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5
I2C_FREQ = 400000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 等待系统稳定
time.sleep(3)
print("FreakStudio: MMC5603 magnetometer initialization and I2C scanner")

# 初始化I2C总线（使用SoftI2C兼容RP2040）
i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)

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
sensor = None
for device in devices_list:
    if device in TARGET_SENSOR_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 自动识别并初始化对应传感器
            sensor = mmc5603.MMC5603(i2c=i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标设备，抛出异常
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================

# 主循环：每秒读取磁场和温度数据并打印
while True:
    mag_x, mag_y, mag_z = sensor.magnetic
    print(f"X:{mag_x:.2f}, Y:{mag_y:.2f}, Z:{mag_z:.2f} uT")
    temp = sensor.temperature
    print(f"Temperature: {temp:.2f}°C")
    print()
    time.sleep(1.0)
