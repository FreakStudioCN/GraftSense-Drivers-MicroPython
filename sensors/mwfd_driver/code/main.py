# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/4/3 下午2:30
# @Author  : hogeiha
# @File    : main.py
# @Description : MWFD水流气泡探测器中断与轮询示例程序

# ======================================== 导入相关模块 =========================================
from machine import Pin
from mwfd import MWFD
import time

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================
def on_state_change(state):
    """
    中断回调函数，当传感器状态变化时自动触发
    Args:
        state (bool): True表示气泡/缺液，False表示正常液体

    Raises:
        无

    Notes:
        该函数由中断服务程序调用，应保持简洁快速

    ==========================================
    Interrupt callback function, automatically triggered when sensor state changes
    Args:
        state (bool): True for bubble/lack of liquid, False for normal liquid

    Raises:
        None

    Notes:
        This function is called by interrupt service routine, keep it short and fast
    """
    # 根据状态打印不同信息
    if state:
        print("[Interrupt] Warning: Bubble or lack of liquid")
    else:
        print("[Interrupt] Normal liquid")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================
# 等待3秒让系统稳定
time.sleep(3)
# 打印启动标识
print("FreakStudio: MWFD sensor demo started")

# 初始化传感器引脚（GPIO15，输入模式，内部下拉）
sensor_pin = Pin(15, Pin.IN, Pin.PULL_DOWN)

# 创建MWFD驱动实例
sensor = MWFD(sensor_pin)

# 启用中断，绑定回调函数
sensor.irq(callback=on_state_change)

# ========================================  主程序  ============================================
# 主循环：主动轮询读取传感器状态并打印
while True:
    # 读取当前状态
    state = sensor.read()
    # 根据状态输出信息
    if state:
        print("[Polling] Warning: Bubble or lack of liquid")
    else:
        print("[Polling] Normal liquid")
    # 延时200毫秒
    time.sleep(0.2)
