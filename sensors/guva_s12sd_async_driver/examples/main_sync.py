# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/24 下午3:37
# @Author  : 缪贵成
# @File    : main.py
# @Description : uv紫外线传感器驱动测试文件，测试等级理论上来讲有11个

# ======================================== 导入相关模块 =========================================

import time
from guva_s12sd import GUVA_S12SD

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ========================================初始化配置 =============================================

time.sleep(3)
print("FreakStudio:  UV Sensor (GUVA-S12SD) Test Starting ")

# 初始化传感器 (GP26 -> ADC0)
sensor = GUVA_S12SD(26)

# ======================================== 主程序 ===============================================

try:
    while True:
        try:
            voltage = sensor.voltage
            uvi = sensor.uvi
            print(f"Voltage: {voltage:.3f} V | UV Index: {uvi:.2f}")
        except RuntimeError as e:
            print(f"[Error] Failed to read sensor data: {e}")

        time.sleep(0.2)

except ValueError as e:
    print(f"[Critical Error] Sensor initialization failed: {e}")
except Exception as e:
    print(f"[Unexpected Error] {e}")
