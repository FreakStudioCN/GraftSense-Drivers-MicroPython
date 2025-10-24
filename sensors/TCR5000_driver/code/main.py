# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/9/4 上午9:44
# @Author  : 缪贵成
# @File    : main.py
# @Description : 单路循迹模块驱动测试文件

# ======================================== 导入相关模块 =========================================

import time
from tcr5000 import TCR5000

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def on_change(value: int) -> None:
    """
    TCR5000 电平变化回调函数，在传感器电平变化时触发。

    Args:
        value (int): 当前电平，0=黑线，1=白底。

    Notes:
        回调通过 micropython.schedule 调度到主循环执行，避免在 ISR 中执行耗时操作。
        用户可以在回调中处理传感器状态变化，例如打印或控制马达。

    ==========================================

    TCR5000 level change callback, triggered on sensor level change.

    Args:
        value (int): Current pin value, 0=black line, 1=white background.

    Notes:
        Callback is scheduled via micropython.schedule to main loop context, avoiding ISR execution.
        User can handle sensor state changes here, e.g., print or motor control.
    """
    print("Callback triggered, value =", value)

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio:Single-channel tracking module test")
# 初始化 TCR5000 传感器
sensor = TCR5000(pin=6)
# 注册回调函数
sensor.set_callback(on_change)

# ========================================  主程序  ===========================================

try:
    while True:
        val = sensor.read()
        print("Current value:", val)
        time.sleep(1)

except KeyboardInterrupt:
    sensor.deinit()
    print("Program interrupted, resources released.")

