# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:20
# @Author  : 缪贵成
# @File    : main.py
# @Description :基于NE555芯片的雾化模块驱动

# ======================================== 导入相关模块 =========================================

import time
from ne555_atomization import Atomization

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio:Testing the NE555-based atomization module")
# 假设 GPIO2 控制雾化模块
atomizer = Atomization(pin=2)

# ========================================  主程序  ============================================

try:
    while True:
        print("turn on")
        atomizer.on()
        print("status:", atomizer.is_on())
        time.sleep(3)

        print("turn off...")
        atomizer.off()
        print("status:", atomizer.is_on())
        time.sleep(3)

        print("toggle...")
        atomizer.toggle()
        print("status:", atomizer.is_on())
        time.sleep(3)

except KeyboardInterrupt:
    print("test stop")
