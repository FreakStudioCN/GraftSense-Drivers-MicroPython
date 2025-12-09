# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/29 下午6:47
# @Author  : 缪贵成
# @File    : main1.py
# @Description : 红外人体热释传感器驱动测试文件

# ======================================== 导入相关模块 =========================================\

from pir_sensor import PIRSensor
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def motion_callback():
    """
    回调函数

    ==========================================

    callback function
    """
    print("Motion detected!")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio : Infrared human body pyro-release sensor test")

# 创建红外人体热释传感器对象
pir = PIRSensor(pin=6, callback=motion_callback)

# ========================================  主程序  ============================================

# 提示用户靠近
print("Waiting for motion...")
# 阻塞等待，无超时
detected = pir.wait_for_motion(timeout=20)

if detected:
    # 阻塞等待检测到运动
    print("Motion detected via blocking wait!")
else:
    print("Timeout, no motion detected.")