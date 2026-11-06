# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : direction_switch.py
# @Description : Explicit bench transition: software disable, confirmed off, then enable.
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
from tuning_profile import prime_integral


# ======================================== 全局变量 ========================================
# ======================================== 功能函数 ========================================
def disable_software(controller: object) -> None:
    """Disable/reset every PID without writing the PWM device."""
    error = None
    for index, pid in enumerate(controller._pids):
        try:
            pid.set_enabled(False)
            controller._pwms[index] = 0
        except Exception as exc:
            if error is None:
                error = exc
    if error is not None:
        raise error


def emergency_stop(controller: object, writer: object, parts: object = None) -> None:
    """Immediate best effort: always attempt hardware stop even if PID disable fails."""
    error = None
    begin = time.ticks_us()
    try:
        disable_software(controller)
    except Exception as exc:
        error = exc
    if parts is not None:
        parts[0] = time.ticks_diff(time.ticks_us(), begin)
    begin = time.ticks_us()
    try:
        writer.stop()
    except Exception as exc:
        if error is None:
            error = exc
    if parts is not None:
        parts[1] = time.ticks_diff(time.ticks_us(), begin)
    if error is not None:
        raise error


def switch_reference(controller: object, writer: object, targets: tuple, optimized: bool, parts: list) -> None:
    """Fill timing slots 0..4: software, off, duplicate legacy stop, gap, setup.

    Only a successful off-frame write AND register readback permit re-enabling.
    Hardware errors preserve the original exception after immediate stop attempts.
    """
    try:
        if optimized:
            begin = time.ticks_us()
            disable_software(controller)
            parts[0] = time.ticks_diff(time.ticks_us(), begin)
            begin = time.ticks_us()
            writer.confirmed_off()
            parts[1] = time.ticks_diff(time.ticks_us(), begin)
            begin = time.ticks_us()
            time.sleep_us(200)
            parts[3] = time.ticks_diff(time.ticks_us(), begin)
        else:
            begin = time.ticks_us()
            writer.stop()
            parts[1] = time.ticks_diff(time.ticks_us(), begin)
            begin = time.ticks_us()
            controller.stop_all()
            parts[2] = time.ticks_diff(time.ticks_us(), begin)
        begin = time.ticks_us()
        controller.set_target_rpms(targets)
        controller.start_all()
        prime_integral(controller, targets)
        parts[4] = time.ticks_diff(time.ticks_us(), begin)
    except BaseException:
        try:
            emergency_stop(controller, writer)
        except Exception:
            pass
        raise


# ======================================== 自定义类 ========================================
# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
