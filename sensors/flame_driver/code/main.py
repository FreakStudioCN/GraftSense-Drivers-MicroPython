# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/23 下午5:55
# @Author  : 缪贵成
# @File    : main.py
# @Description : 火器驱焰传感动测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import Pin
from flame_sensor import FlameSensor

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 =============================================


def flame_detected_callback() -> None:
    """
    火焰检测回调函数。当数字引脚 DO 触发时，由 micropython.schedule 调用。

    Notes:
        回调在主线程中执行，可以安全进行打印或 LED 控制。

    ==========================================

    Callback function triggered on flame detection.
    Called by micropython.schedule when digital pin DO triggers.

    Notes:
        Safe to perform printing or LED control in main thread.
    """
    print("Flame detected!")


# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

print("FreakStudio:Testing Flame Sensor")
time.sleep(3)

# 初始化火焰传感器对象，假设模拟输出引脚为 26，数字输出引脚为 19
flame_sensor = FlameSensor(analog_pin=26, digital_pin=19, callback=flame_detected_callback)
# 启用数字引脚中断
flame_sensor.enable()

# ======================================== 主程序 ==============================================

print("=== Flame Sensor Initialized. Monitoring AO voltage... ===")

try:
    while True:
        # 获取 AO 模拟值并转换为电压
        voltage = flame_sensor.get_voltage()
        print("AO Voltage: {:.2f} V".format(voltage))
        time.sleep(1)
except KeyboardInterrupt:
    print("=== Test Stopped by User ===")
    flame_sensor.disable()
