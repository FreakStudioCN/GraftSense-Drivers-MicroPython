# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 上午11:22
# @Author  : ben0i0d
# @File    : main.py
# @Description : 触控按键驱动测试文件

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入按钮驱动模块
from touchkey import TouchKey

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def on_press():
    print("Button pressed")

def on_release():
    print("Button released")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio:Testing Button")

# 创建 TouchKey 对象
button = TouchKey(pin_num=6, idle_state=TouchKey.high, debounce_time=50, press_callback=on_press, release_callback=on_release)

# ========================================  主程序  ============================================

try:
    while True:
        state = button.get_state()
        print("Current button state:", "Pressed" if state else "Released")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exit button test program")