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

vl530_addr = None

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: Testing VL53L0X Time-of-Flight sensor")

# 初始化 I2C (Raspberry Pi Pico 使用 I2C0，默认引脚 GP8=SDA, GP9=SCL)
i2c = machine.I2C(0, scl=5, sda=4, freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list:list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    if 0x60 <= device <= 0x7A:
        print("I2c hexadecimal address:", hex(device))
        vl530_addr = device

# 初始化 VL53L0X 传感器
tof = VL53L0X(i2c, vl530_addr)
print("VL53L0X initialized successfully")

# ======================================== 主程序 ==============================================
try:
    # 设置为连续测量模式，周期 50ms
    tof.start()
    while True:
        # 读取距离，单位 mm
        distance = tof.read()
        if distance > 0 and distance < 2000:
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
