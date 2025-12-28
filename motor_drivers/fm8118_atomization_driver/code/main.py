# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/9 上午10:20
# @Author  : 缪贵成
# @File    : main.py
# @Description :基于FM8118芯片的雾化模块驱动

# ======================================== 导入相关模块 =========================================

import time
from fm8118_atomization import FM8118_Atomization

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio:Testing the FM8118-based atomization module")

# 使用 GPIO6 控制雾化模块
atomizer = FM8118_Atomization(pin=6)

# ========================================  主程序  ============================================

try:
    while True:
        print("turn on")
        atomizer.on()
        print("status:", atomizer.is_on())
        time.sleep(10)

        print("turn off...")
        atomizer.off()
        print("status:", atomizer.is_on())
        time.sleep(10)

        print("toggle...")
        atomizer.toggle()
        print("status:", atomizer.is_on())
        time.sleep(10)

except KeyboardInterrupt:
    print("test stop")
