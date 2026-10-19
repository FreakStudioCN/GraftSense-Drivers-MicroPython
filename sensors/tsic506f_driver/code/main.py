# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/07 11:10
# @Author  : Robert Hammelrath
# @File    : main.py
# @Description : 测试 TSIC506F 驱动类的示例代码
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time

from machine import Pin
from tsic506 import TSIC506F, TSIC506FNotRunning

# ======================================== 全局变量 ============================================
# 传感器数据引脚
DATA_PIN = 6
# 数据打印间隔（ms）
print_interval_ms = 500

# 驱动实例占位变量，在初始化配置区创建
tsic506f = None
# 上次打印时间戳（ms）
last_print_time = 0

# ======================================== 功能函数 ============================================


def print_temperature(celsius: float) -> None:
    """
    打印温度值
    Args:
        celsius (float): 摄氏温度值
    Notes:
        - 仅在主循环的低频打印分支中调用
    """
    print("TSic506F temperature: %.2f C" % celsius)


# ======================================== 自定义类 ============================================
# 无自定义类，全部逻辑在初始化配置区和主程序中

# ======================================== 初始化配置 ==========================================
# 上电稳定延时
time.sleep(3)
print("FreakStudio: Testing TSIC506F ZACwire temperature sensor on RP2040...")

# 先下拉数据脚再切换为输入采样，降低首次启动抖动
data_pin = Pin(DATA_PIN, Pin.OUT, value=0)
time.sleep_ms(10)
data_pin.init(Pin.IN)

# 创建 TSIC506F 驱动实例并立即启动双状态机
# 使用 9 点中值滤波，降低 ZACwire 偶发抖动
tsic506f = TSIC506F(pin=data_pin, sm=(0, 1), start=True, filter=9)

# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval_ms:
            try:
                print_temperature(tsic506f.T())
            except TSIC506FNotRunning:
                # 首帧尚未就绪，稍后重试，避免输出无效值
                pass
            last_print_time = current_time
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as error:
    print("Hardware communication error: %s" % str(error))
except Exception as error:
    print("Unknown error: %s" % str(error))
finally:
    print("Cleaning up resources...")
    try:
        if tsic506f is not None:
            tsic506f.deinit()
            del tsic506f
    except Exception as error:
        print("Cleanup error: %s" % str(error))
    print("Program exited")
