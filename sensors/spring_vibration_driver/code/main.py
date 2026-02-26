# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/22 下午4:08
# @Author  : 缪贵成
# @File    : main.py
# @Description : 弹簧震动开关驱动测试文件

# ======================================== 导入相关模块 ==========================================

import time
from machine import Pin
from vibration_sensor import VibrationSensor

# ======================================== 全局变量 =============================================

# 上次触发的时间戳
last_irq_time = 0
# 50ms 节流
THROTTLE_MS = 50

# ======================================== 功能函数 ==============================================


def vibration_callback() -> None:
    """
    震动回调函数，在检测到震动时触发。

    Notes：
        该函数由中断触发，通过 micropython.schedule 调度执行。
        采用节流措施，每50ms只处理一次中断，其他忽略。

    ==========================================

    Vibration callback function, triggered when vibration is detected.

    Notes:
        This function is called from interrupt, scheduled via micropython.schedule.
        Adopt throttling measures, handling interrupts only once every 50ms, ignoring the rest.
    """
    global last_irq_time
    now = time.ticks_ms()
    if time.ticks_diff(now, last_irq_time) > THROTTLE_MS:
        last_irq_time = now
        print("Vibration detected callback triggered!")
        # 否则忽略此次中断触发


# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ============================================

# 上电延时，确保硬件稳定
time.sleep(3)
print("FreakStudio: Vibration Sensor Test Start")
# 初始化震动传感器，GPIO 引脚 15 输入，回调函数处理
sensor = VibrationSensor(pin=Pin(6), callback=vibration_callback, debounce_ms=10)
sensor.init()
print("Sensor initialized with callback and debounce 50ms.")

# ======================================== 主程序 ===============================================

try:
    start_time = time.ticks_ms()
    while True:
        # 轮询读取传感器状态
        current_state: bool = sensor.read()
        print(f"Current vibration state: {current_state}")

        # 每隔 2 秒打印状态字典
        if time.ticks_diff(time.ticks_ms(), start_time) > 2000:
            status: dict = sensor.get_status()
            print(f"Sensor status: {status}")
            start_time = time.ticks_ms()

        time.sleep(0.2)

except KeyboardInterrupt:
    # 用户中断退出
    print("KeyboardInterrupt detected. Exiting test...")

finally:
    # 安全释放资源
    sensor.deinit()
    print("Sensor deinitialized. Test completed.")
