# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/11/4 下午5:33
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试ba111_tds水质检测代码
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

from ba111_tds import BA111TDS
import time
from machine import Pin, UART

# ======================================== 全局变量 ============================================

uart = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))
sensor = BA111TDS(uart)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================

time.sleep(3)
print("FreakStudio: test Light Intensity Sensor now")

# 设置参数（如果需要）
sensor.set_ntc_resistance(10000)
sensor.set_ntc_b_value(3950)

input("基线校探头放入25C+-5C的纯净水中，按下任意键校准")
# 校准
sensor.calibrate()
print("校准成功")
while True:
    
    # 读取数据
    result = sensor.detect()
    if result:
        tds, temp = result
        print(f"TDS: {tds}ppm, 温度: {temp}℃")

