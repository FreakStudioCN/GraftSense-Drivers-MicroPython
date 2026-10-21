# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 上午11:41
# @Author  : 缪贵成
# @File    : main.py
# @Description : 震动马达驱动测试文件

# ======================================== 导入相关模块 =========================================

import time
from vibration_motor import VibrationMotor

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def demo_full() -> None:
    """
    震动马达全速运行演示 2 秒。
    Notes:
        调用 motor.on() 开启全速，sleep 2 秒后关闭。
        可用于 REPL 交互测试马达全速运行。

    ==========================================

    Demonstrate vibration motor running at full speed for 2 seconds.
    Notes:
        Uses motor.on() to run at full speed, then stops after 2 seconds.
        Suitable for interactive REPL testing.
    """
    print(">>> Motor running at full speed for 2 seconds")
    motor.on()
    time.sleep(2)
    motor.off()
    print(">>> Motor stopped")


def demo_half() -> None:
    """
    震动马达半速运行演示 2 秒。

    Notes:
        调用 motor.set_brightness(512) 设置半速，sleep 2 秒后关闭。
        可用于 REPL 交互测试马达中速运行。

    ==========================================

    Demonstrate vibration motor running at half speed for 2 seconds.

    Notes:
        Uses motor.set_brightness(512) for half speed, then stops after 2 seconds.
        Suitable for interactive REPL testing.
    """
    print(">>> Motor running at half speed for 2 seconds")
    motor.set_brightness(512)
    time.sleep(2)
    motor.off()
    print(">>> Motor stopped")


def demo_low() -> None:
    """
    震动马达低速运行演示 2 秒。

    Notes:
        调用 motor.set_brightness(400) 设置低速，sleep 2 秒后关闭。
        可用于 REPL 交互测试马达低速运行。

    ==========================================

    Demonstrate vibration motor running at low speed for 2 seconds.

    Notes:
        Uses motor.set_brightness(400) for low speed, then stops after 2 seconds.
        Suitable for interactive REPL testing.
    """
    print(">>> Motor running at low speed for 2 seconds")
    motor.set_brightness(400)
    time.sleep(2)
    motor.off()
    print(">>> Motor stopped")


def show_methods() -> None:
    """
    打印 REPL 可用操作方法列表。

    Notes:
        显示 motor 对象的方法以及 demo_* 演示函数。
        适合用户在 REPL 中快速了解可用操作。

    ==========================================

    Print the list of available REPL methods.

    Notes:
        Shows motor object methods and demo_* functions.
        Useful for interactive REPL guidance.
    """
    print("Available methods:")
    print("motor.on()")
    print("motor.off()")
    print("motor.toggle()")
    print("motor.set_brightness(duty)")
    print("motor.get_state()")
    print("demo_full()")
    print("demo_half()")
    print("demo_low()")
    print("show_methods()")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio:Vibration motor test")

# 默认引脚 12，PWM 频率 1000Hz
motor = VibrationMotor(pin=6, pwm_freq=1000)

# ========================================  主程序  ===========================================

# 打印可以操作的方法
show_methods()
# 操作马达以不同强度工作
demo_full()
demo_half()
demo_low()
