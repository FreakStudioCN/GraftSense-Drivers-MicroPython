# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/1 上午11:22
# @Author  : ben0i0d
# @File    : main.py
# @Description : dht22驱动测试文件 测试输出温湿度
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

import dht22
from machine import Pin
from time import sleep

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
# 初始化单总线通信引脚，下拉输出
DHT22_PIN = Pin(13, Pin.OUT, Pin.PULL_DOWN)
# 初始化DHT11实例
dht22 = dht22.DHT22(DHT22_PIN)

# ========================================  主程序  ============================================

while True:
    # 读取温湿度数据
    temperature = dht22.get_temperature()
    humidity = dht22.get_humidity()
    # 打印温湿度数据
    print("temperature: {}℃, humidity: {}%".format(temperature, humidity))
    # 等待2秒
    time.sleep(2)