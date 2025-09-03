# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/08/20 10:21
# @Author  : 缪贵成
# @File    : main.py
# @Description : 测试MG系列气体传感器模块驱动程序

# ======================================== 导入相关模块 =========================================

from machine import Pin, ADC
import time
from time import sleep
from mgx import MGX

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# 用户回调函数
def mg_callback(voltage: float) -> None:
    """
    当比较器引脚触发中断时调用该函数，打印当前电压值。

    Args:
        voltage (float): 电压值 (单位: V)。

    ==========================================

    This function is called when the comparator pin triggers an IRQ,
    and prints the measured voltage.

    Args:
        voltage (float): Voltage value in volts.

    """
    print("[IRQ] Voltage: {:.3f} V".format(voltage))

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# 上电延时3s
time.sleep(3)
# 打印调试消息
print("Measuring Gas Concentration with MG Series Gas Sensor Modules")

# Pico ADC0 (GPIO26)
adc = ADC(Pin(26))
# Comparator output (GPIO15, optional)
comp = Pin(15, Pin.IN)
mg = MGX(adc, comp, mg_callback, rl_ohm=10000, vref=3.3)

# 选择内置多项式（MG811,MG812）
mg.select_builtin("MG811")

# 传入自定义的多项式
# mq.set_custom_polynomial([1.0, -2.5, 3.3])

# ========================================  主程序  ===========================================

print("===== MG Sensor Test Program Started =====")
try:
    while True:
        # 读取电压
        v = mg.read_voltage()
        print("Voltage: {:.3f} V".format(v))

        # 读取 ppm（5 次采样，间隔 200 ms）
        ppm = mg.read_ppm(samples=5, delay_ms=200)
        print("Gas concentration: {:.2f} ppm".format(ppm))

        print("-" * 40)
        # 主循环间隔
        sleep(2)
except KeyboardInterrupt:
    print("User interrupted, exiting program...")
finally:
    mg.deinit()
    print("Sensor resources released.")
