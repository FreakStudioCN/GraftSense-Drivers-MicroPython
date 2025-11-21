# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 上午9:48
# @Author  : 缪贵成
# @File    : main.py
# @Description : 霍尔传感器驱动测试文件(数字）

# ======================================== 导入相关模块 ==========================================

import time
from hall_sensor_oh34n import HallSensorOH34N

# ======================================== 全局变量 =============================================

# 消抖标志位
flag = False
# 上一次触发时间
last_time = 0
# 防抖间隔 200ms
DEBOUNCE_MS = 200

# ======================================== 功能函数 =============================================

def hall_callback() -> None:
    """
        霍尔传感器的中断回调函数。
        当检测到磁场变化时触发，并打印提示信息。

    Notes:
        此回调函数由 IRQ 中断触发，并通过 micropython.schedule 调度。
        避免在回调中加入耗时或阻塞操作。

    ==========================================

        Interrupt callback for Hall sensor.
        Triggered when magnetic field change is detected, prints notification.

    Notes:
        This callback is triggered by IRQ and scheduled via micropython.schedule.
        Avoid long-running or blocking operations in the callback.
    """
    global flag, last_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_time) > DEBOUNCE_MS:
        flag = True
        last_time = now

# ======================================== 自定义类 ==============================================

# ======================================== 初始化配置 ============================================

# 上电延时
time.sleep(3)
print("FreakStudio: Hall Sensor OH34N Test Start ")

# 初始化霍尔传感器（GP6 引脚）
sensor = HallSensorOH34N(pin=6, callback=hall_callback)

# 启用中断检测
sensor.enable()
print("Interrupt detection enabled.")

# ======================================== 主程序 ===============================================

try:
    while True:
        if flag:
            print("Callback: Magnetic field detected!")
            flag = False
        state = sensor.read()
        print(f"Magnetic field detected: {state}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Test stopped by user.")
    sensor.disable()
    print("Interrupt detection disabled.")
