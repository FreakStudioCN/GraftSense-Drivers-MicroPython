# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:00
# @Author  : 侯钧瀚
# @File    : main.py
# @Description : PCA968516路PWM驱动板示例程序

# ======================================== 导入相关模块 =========================================
#导入时间模块
import time
# 导入MicroPython标准库模块
from machine import Pin, I2C
# 导入总线舵机控制器模块
from bus_servo import BusPWMServoController
# 导入PCA9685模块
from pca9685 import PCA9685
# ======================================== 全局变量 ============================================
# ======================================== 全局变量 ============================================

# 自动扫描 PCA9685 地址（0x40~0x4F）
addr = 0x40

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================
# 上电延时3s
time.sleep(3)
# 打印调试消息
print("FreakStudio: Using PCA9685 to control the angles of two servos")

# 自动扫描 PCA9685 地址（0x40~0x4F）
i2c = I2C(id=0, sda=Pin(4), scl=Pin(5), freq=400000)
for d in i2c.scan():
    if 0x40 <= d <= 0x4F:
        addr = d
        break

pca = PCA9685(i2c, addr)

# 创建控制器（50Hz 常用于舵机）
srv = BusPWMServoController(pca, freq=50)

# --------------- 绑定两个通道 ---------------
# 通道0：180° 舵机，标准 500~2500us，1500us 为中立
srv.attach_servo(0, BusPWMServoController.SERVO_180, min_us=500, max_us=2500, neutral_us=1500)
# 通道1：360° 连续舵机，自带停转点在 1500us 附近；如需反向可 reversed=True
srv.attach_servo(1, BusPWMServoController.SERVO_360, min_us=1000, max_us=2000, neutral_us=1500)

# ========================================  主程序  ===========================================

# --------------- 演示 180° 角度控制 ---------------
srv.set_angle(0, 0.0)          # 转到 0°
time.sleep(1)
srv.set_angle(0, 90.0, speed_deg_per_s=120)  # 以约 120°/s 平滑转到 90°
time.sleep(1)
srv.set_angle(0, 180.0, speed_deg_per_s=180) # 平滑转到 180°
time.sleep(1)
srv.stop(0)                     # 回中或停

# --------------- 演示 360° 速度控制 ---------------
srv.set_speed(1, +0.6)          # 顺时针中速
time.sleep(2)
srv.set_speed(1, -0.6)          # 反向中速
time.sleep(2)
srv.set_speed(1, 0.0)           # 停止（1500us）
time.sleep(0.5)
srv.detach_servo(1)             # 关闭输出并解除绑定