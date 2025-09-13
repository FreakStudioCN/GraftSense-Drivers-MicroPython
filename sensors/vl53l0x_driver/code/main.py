# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 上午10:39
# @Author  : 缪贵成
# @File    : main.py
# @Description : 基于vl53l0x的激光测距模块驱动测试文件

# ======================================== 导入相关模块 =========================================

import time
import machine
from vl53l0x import VL53L0X

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: Testing VL53L0X Time-of-Flight sensor")

# 初始化 I2C (Raspberry Pi Pico 使用 I2C0，默认引脚 GP8=SDA, GP9=SCL)
i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8), freq=400000)

# 扫描 I2C 设备，确保传感器存在
devices = i2c.scan()
if not devices:
    print("No I2C devices found. Please check wiring!")
    raise SystemExit(1)
else:
    print("Found I2C devices:", [hex(dev) for dev in devices])

# 初始化 VL53L0X 传感器
tof = VL53L0X(i2c)
print("VL53L0X initialized successfully")

# ======================================== 主程序 ==============================================
try:
    # 设置为连续测量模式，周期 50ms
    tof.start()
    while True:
        # 读取距离，单位 mm
        distance = tof.read()
        if distance > 0:
            print("Distance: %d mm" % distance)
        else:
            print("Out of range or read error")
        time.sleep(0.8)

except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    # 停止测量
    tof.stop()
    print("Testing completed")
