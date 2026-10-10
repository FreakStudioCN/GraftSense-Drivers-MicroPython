# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/27 下午8:45
# @Author  : Jose D. Montoya
# @File    : main.py
# @Description : H3LIS200DL加速度传感器数据读取程序

# ======================================== 导入相关模块 =========================================
import time
from machine import Pin, I2C
from micropython_h3lis200dl import h3lis200dl

# ======================================== 全局变量 ============================================
# 定义传感器目标I2C地址列表
TARGET_H3LIS200DL_ADDRS = [0x18, 0x19]

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================
time.sleep(3)
print("FreakStudio: H3LIS200DL accelerometer initialization")

# 初始化I2C总线
i2c_bus = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# 扫描I2C总线上的所有设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查是否扫描到I2C设备
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 初始化传感器对象占位符
sensor = None

# 遍历设备列表匹配传感器地址
for device in devices_list:
    if device in TARGET_H3LIS200DL_ADDRS:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化传感器
            sensor = h3lis200dl.H3LIS200DL(i2c_bus)
            print("Sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标传感器
    raise Exception("No target sensor device found in I2C bus")

# ========================================  主程序  ============================================
while True:
    # 获取三轴加速度数据
    accx, accy, accz = sensor.acceleration
    # 打印格式化的加速度数据
    print(f"x:{accx:.2f}g, y:{accy:.2f}g, z:{accz:.2f}g")
    print()
    # 延时0.5秒
    time.sleep(0.5)
