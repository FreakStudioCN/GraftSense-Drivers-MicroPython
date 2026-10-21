# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/21 下午
# @Author  : hogeiha
# @File    : main.py
# @Description : MiCS6814 CO、NH3、NO2 三通道 ADC 读取示例

# ======================================== 导入相关模块 =========================================

import time
from mics6814 import MICS6814

# ======================================== 全局变量 ============================================

# CO 通道连接到 Pico GPIO26
CO_PIN = 26

# NH3 通道连接到 Pico GPIO27
NH3_PIN = 27

# NO2 通道连接到 Pico GPIO28
NO2_PIN = 28

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: MICS6814 CO NH3 NO2 ADC sensor")

# 创建 MiCS6814 三通道 ADC 采集对象
gas = MICS6814(CO_PIN, NH3_PIN, NO2_PIN)

# ========================================  主程序  ============================================

try:
    while True:
        # 读取 CO、NH3、NO2 三个通道的电阻、电压和原始 ADC 值
        readings = gas.read_all()

        # 打印传感器读数
        print(readings)

        # 每秒读取一次传感器
        time.sleep(1)
except KeyboardInterrupt:
    pass
