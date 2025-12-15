# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 上午11:53
# @Author  : 缪贵成
# @File    : main.py
# @Description : 大功率单颗led驱动测试文件，包括开关，切换，pwm控制亮度

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time
# 导入第三方模块
from led_single_power import PowerLED

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
print("FreakStudio: Test high-power LED lights")

# 创建实例，使用GP14引脚
led = PowerLED(pin=14, pwm_freq=1000)

# ======================================== 主程序 ==============================================

# 打开 LED
try:
    led.on()
    print("LED turned ON.")
    time.sleep(4)
except RuntimeError as e:
    print("Error turning LED ON:", e)

# 关闭 LED
try:
    led.off()
    print("LED turned OFF.")
    time.sleep(4)
except RuntimeError as e:
    print("Error turning LED OFF:", e)

# 切换 LED 状态
try:
    led.toggle()
    print("LED toggled. Current state:", "ON" if led.get_state() else "OFF")
    time.sleep(1)
except RuntimeError as e:
    print("Error toggling LED:", e)

# 设置亮度逐步调光
try:
    for duty in range(0, 1024, 2):
        led.set_brightness(duty)
        print(f"LED brightness set to {duty}/1023. Current state:", "ON" if led.get_state() else "OFF")
        time.sleep(0.5)
except (ValueError, RuntimeError) as e:
    print("Error setting brightness:", e)

# 最终关闭 LED
try:
    led.off()
    print("LED turned OFF at the end of test.")
except RuntimeError as e:
    print("Error turning LED OFF at the end:", e)

print(" PowerLED Test End ")
