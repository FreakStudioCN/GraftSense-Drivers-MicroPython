# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/22 上午9:42
# @Author  : 缪贵成
# @File    : main.py
# @Description : 光耦隔离 MOS 单电机驱动测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin, PWM
from opto_mos_simple import OptoMosSimple

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时
time.sleep(3)
print("FreakStudio:  OptoMosSimple Test Start ")
# 创建 PWM 对象，GPIO6 输出
pwm = PWM(Pin(6))
# Set PWM frequency to 1kHz
pwm.freq(1000)
print("PWM object created on Pin 6 with 1kHz frequency.")

# 创建驱动实例
driver = OptoMosSimple(pwm)
print("Driver object created.")

# 初始化驱动
driver.init()
print("[init] Initialized ->", driver.get_status())

# ======================================== 主程序 ===============================================

# 测试 set_duty 方法
print("[set_duty] Set duty=10000")
driver.set_duty(10000)
print("Status:", driver.get_status())

print("[set_duty] Set duty=70000 (out of range, auto clipped)")
driver.set_duty(70000)
print("Status:", driver.get_status())

# 测试 set_percent 方法
print("[set_percent] Set 25% duty cycle")
driver.set_percent(25.0)
print("Status:", driver.get_status())

print("[set_percent] Set 150% duty cycle (out of range, auto clipped)")
driver.set_percent(150.0)
print("Status:", driver.get_status())

# 测试 full_on 方法
print("[full_on] Full ON")
driver.full_on()
print("Status:", driver.get_status())
time.sleep(5)

# 测试 off 方法
print("[off] Turn OFF")
driver.off()
print("Status:", driver.get_status())
time.sleep(10)

# 测试 inverted 模式（创建新的 PWM 对象）
print("[inverted] Testing inverted mode")
pwm_inv = PWM(Pin(16))  # 使用不同 GPIO 避免与 driver 冲突
pwm_inv.freq(1000)
driver_inv = OptoMosSimple(pwm_inv, inverted=True)
driver_inv.init()
driver_inv.set_percent(30.0)
print("Inverted 30% ->", driver_inv.get_status())
driver_inv.full_on()
print("Inverted full_on ->", driver_inv.get_status())
driver_inv.off()
print("Inverted off ->", driver_inv.get_status())

# 释放资源
print("[deinit] Release resources")
driver.deinit()
driver_inv.deinit()
print("PWM released.")

print("=== OptoMosSimple Test End ===")
