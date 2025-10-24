# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/28 上午11:22
# @Author  : 缪贵成
# @File    : main.py
# @Description : pwm驱动散热风扇驱动测试文件 测试了不同的占空比

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入风扇驱动模块
from fan_pwm import FanPWM

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio:Testing PWM cooling fans")

# 创建一个 FANPWM 对象
fan = FanPWM(pin=6)

# ========================================  主程序  ============================================

try:
    print("\n[Step 1] Turning fan ON (full speed)...")
    fan.on()
    print(f"Current duty: {fan.get_speed()}")
    time.sleep(5)

    print("\n[Step 2] Turning fan OFF...")
    fan.off()
    print(f"Current duty: {fan.get_speed()}")
    time.sleep(5)

    # 测试不同占空比
    for duty in [256, 512, 768, 1023]:
        print(f"\n[Step] Setting fan duty to {duty}...")
        fan.set_speed(duty)
        print(f"Current duty: {fan.get_speed()}")
        time.sleep(5)

    print("\n[Step 3] Testing digital property (Pin object)...")
    pin_obj = fan.digital
    print(f"Pin object: {pin_obj}")
    time.sleep(5)

    print("\n[Step 4] Testing pwm property (PWM object)...")
    pwm_obj = fan.pwm
    print(f"PWM object: {pwm_obj}")
    time.sleep(5)

except KeyboardInterrupt:
    print("\nTest interrupted by user.")

finally:
    print("\n[Cleanup] Turning fan OFF...")
    fan.off()
    print("Test complete.")
