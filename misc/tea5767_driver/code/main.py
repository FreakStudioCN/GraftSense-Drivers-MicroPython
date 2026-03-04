# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 下午3:00
# @Author  : hogeiha
# @File    : main.py
# @Description : FM radio controller test  Initialize FM radio module and read status information

# ======================================== 导入相关模块 =========================================
# 导入FM radio模块
from machine import Pin, SoftI2C
from tea5767 import Radio
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: FM radio controller test - Initialize and read status")

i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=400000)

radio = Radio(i2c, freq=106.7)
print('Frequency: FM {}\nReady: {}\nStereo: {}\nADC level: {}'.format(
    radio.frequency, radio.is_ready,  radio.is_stereo, radio.signal_adc_level))