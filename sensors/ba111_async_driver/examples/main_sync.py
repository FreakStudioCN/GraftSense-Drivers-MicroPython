# Python env   : MicroPython v1.26.1
# -*- coding: utf-8 -*-
# @Time    : 2026/1/19 下午5:33
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试ba111_tds水质检测代码

# ======================================== 导入相关模块 =========================================

from ba111_tds import BA111TDS
import time
from machine import Pin, UART

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: test Light Intensity Sensor now")

uart = UART(0, baudrate=9600, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))
sensor = BA111TDS(uart)

# 设置参数（如果需要）
sensor.set_ntc_resistance(10000)
sensor.set_ntc_b_value(3950)

# ========================================  主程序  ============================================

input("Place the baseline calibration probe into pure water at 25°C - 5°C, and press any key to calibrate.")
# 校准
if sensor.calibrate():
    print("Calibration successful")
    while True:
        # 读取数据
        result = sensor.detect()
        if result:
            tds, temp = result
            print(f"TDS: {tds}ppm, temp: {temp}℃")
            time.sleep(1)
else:
    print("Calibration failed")
