# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/1 上午11:22
# @Author  : ben0i0d
# @File    : main.py
# @Description : dht22驱动测试文件 测试输出温湿度

# ======================================== 导入相关模块 =========================================

import dht
from machine import Pin
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时等待设备初始化
time.sleep(3)
# 打印调试信息
print('FreakStudio : Using OneWire to read DHT22 sensor')

# 延时1s，等待DHT22传感器上电完成
time.sleep(1)
# 假设数据脚接 GPIO6
d = dht.DHT22(Pin(6))

# ========================================  主程序  ============================================

while True:
    try:
        d.measure()
        temp = d.temperature()
        hum = d.humidity()
        print("Temperature: %.1f C  Humidity: %.1f %%" % (temp, hum))
    except Exception as e:
        print("Read error:", e)
    time.sleep(2)







