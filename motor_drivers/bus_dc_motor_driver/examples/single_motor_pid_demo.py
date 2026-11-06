# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : single_motor_pid_demo.py
# @Description : 单路独立闭环：30、60、-30 RPM；其他电机保持停止。
# @License : MIT

# ======================================== 导入相关模块 ========================================
from board_setup import run_profile

# ======================================== 全局变量 ========================================
ARM_MOTORS = False
MOTOR_ID = 1
TARGETS = (30, 60, -30)
SECONDS_PER_STAGE = 10


# ======================================== 功能函数 ========================================
def stages() -> tuple:
    if MOTOR_ID not in (1, 2, 3, 4):
        raise ValueError("Motor ID must be 1..4")
    result = []
    for target in TARGETS:
        rpms = [0, 0, 0, 0]
        rpms[MOTOR_ID - 1] = target
        result.append((tuple(rpms), SECONDS_PER_STAGE))
    return tuple(result)


# ======================================== 自定义类 ========================================
# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
if __name__ == "__main__":
    run_profile(stages(), ARM_MOTORS)
