# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/07 20:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : MAX30102驱动示例程序
# ======================================== 导入相关模块 =========================================

from machine import Pin, I2C
from time import sleep
from heartratemonitor import HeartRateMonitor

# ======================================== 全局变量 ============================================

# 创建 I2C 对象
i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
# 初始化心率监测器
hr_monitor = HeartRateMonitor(i2c, sample_rate=100, window_size=10, smoothing_window=5)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

# 模拟数据：通过硬件读取真实的传感器数据
for i in range(100):
    hr_monitor.read_data()  # 读取传感器数据
    heart_rate = hr_monitor.calculate_heart_rate()  # 计算心率
    if heart_rate is not None:
        print(f"Heart Rate: {heart_rate:.0f} BPM")
    else:
        print("Not enough data to calculate heart rate")
    sleep(0.1)  # 模拟采样间隔







