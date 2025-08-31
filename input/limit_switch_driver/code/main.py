# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 上午10:35
# @Author  : 缪贵成
# @File    : main.py
# @Description : 限位开关测试文件

# ======================================== 导入相关模块 =========================================

import time
from limit_switch import LimitSwitch

# ======================================== 全局变量 =============================================

# ======================================== 功能函数 ==============================================

def switch_callback(state: bool):
    """
    用户回调函数，当限位开关状态变化且消抖完成后被调用。

    Args:
        state (bool): True = released（未触发），False = pressed（已触发）

    Notes:
        通过 micropython.schedule 调度执行，安全运行于主线程。
    ==========================================
    User callback function, called after limit switch state change and debounce.

    Args:
        state (bool): True = released (open), False = pressed (closed)

    Notes:
        Scheduled via micropython.schedule, safe in main thread.
    """
    if state:
        print("Limit switch released (open)")
    else:
        print("Limit switch pressed (closed)")

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: Limit switch test")

# 初始化限位开关，设置消抖时间间隔为 50ms
switch = LimitSwitch(pin=19, callback=switch_callback, debounce_ms=50)
# 启用消抖检测
switch.enable()

# ======================================== 主程序 =============================================

try:
    while True:
        state = switch.read()
        if state:
            print("Current state: released (open)")
        else:
            print("Current state: pressed (closed)")
        time.sleep(1)
except KeyboardInterrupt:
    # 停止测试
    print("Test stopped by user.")
    switch.disable()

