# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/05
# @File    : pid_math_test.py
# 作者与许可证：原项目未声明，参见 README。
"""独立 PID 数学自检；可在 PC 或开发板运行，无硬件访问。"""
# ======================================== 导入相关模块 ========================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from pid import PID  # noqa: E402 - local device module path selected above


# ======================================== 全局变量 ========================================
# ======================================== 功能函数 ========================================
def check_pid() -> None:
    pid = PID(kp=2, ki=1, kd=0, dt=0.1, output_limit=(-10, 10), integral_limit=(-2, 2))
    pid.set_target(100)
    assert pid.update(0) == 0
    pid.set_enabled(True)
    for _ in range(30):
        assert pid.update(0) == 10
    assert pid.integral == 2
    pid.set_target(-100)
    for _ in range(30):
        assert pid.update(0, dt=0.1) == -10
    assert pid.integral == -2
    pid.set_enabled(False)
    assert pid.update(0) == 0 and pid.integral == 0
    pid.set_params(kp=1, ki=0, kd=0.1)
    pid.set_target(2)
    pid.set_enabled(True)
    assert abs(pid.update(0, dt=0.1) - 4) < 1e-6
    assert pid.update(0, dt=0) == pid.output
    assert pid.update(0, global_enabled=False) == 0
    pid.reset()
    assert pid.integral == 0 and pid.output == 0
    try:
        PID(dt=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid interval accepted")
    print("PASS: enable, target, gains, P/I/D, limits, dt and reset")


# ======================================== 自定义类 ========================================
# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
if __name__ == "__main__":
    print("FreakStudio: PID math test; no hardware")
    check_pid()
