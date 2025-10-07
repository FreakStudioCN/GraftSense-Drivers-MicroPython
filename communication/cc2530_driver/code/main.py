# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : cc253x_ttl测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import UART,Pin
from cc253x_ttl import CC253xTTL

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio:cc253x_ttl test")

uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
key = Pin(2, mode=Pin.OUT)

# 唤醒
key.value(0)
time.sleep(0.05)
key.value(1)

cor = CC253xTTL(uart0)
env = CC253xTTL(uart1)

# ========================================  主程序  ===========================================

print(cor.read_short_addr())
print(env.read_mac())