# MicroPython v1.23.0
# -*- coding: utf-8 -*-   
# @Time    : 2025/8/23 下午4:08
# @Author  : 缪贵成
# @File    : main.py
# @Description : 滚珠震动传感器驱动测试文件

# ======================================== 导入相关模块 ==========================================

import time
from machine import Pin
from vibration_sensor import VibrationSensor

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 ==============================================
def vibration_callback() -> None:
    """
    震动回调函数，在检测到震动时触发。

    Notes：
        该函数由中断触发，通过 micropython.schedule 调度执行。

    ==========================================

    Vibration callback function, triggered when vibration is detected.

    Notes:
        This function is called from interrupt, scheduled via micropython.schedule.
    """
    print("Vibration detected callback triggered!")

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ============================================

# 上电延时，确保硬件稳定
time.sleep(3)
print("FreakStudio: Vibration Sensor Test Start")
# 初始化震动传感器，GPIO 引脚 6 输入，回调函数处理
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