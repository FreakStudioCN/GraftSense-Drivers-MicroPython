# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : main.py
# @Description : 振动电机异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, PWM
from vibration_motor_async import VibrationMotorAsync

# ======================================== 全局变量 ============================================
MOTOR_PIN = 6
PWM_FREQ = 1000
RUN_TIME_MS = 2000
HALF_DUTY = 512
LOW_DUTY = 400

# ======================================== 功能函数 ============================================
async def run_step(motor: VibrationMotorAsync, duty: int, label: str) -> None:
    """以给定占空比运行振动电机，然后停止。"""
    print(">>> Motor running at %s for 2 seconds" % label)
    await motor.set_brightness_async(duty)
    await asyncio.sleep_ms(RUN_TIME_MS)
    await motor.off_async()
    print(">>> Motor stopped")


async def main() -> None:
    """执行来源示例的全速、半速和低速振动测试。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    pwm = PWM(Pin(MOTOR_PIN, Pin.OUT))
    pwm.freq(PWM_FREQ)
    pwm.duty_u16(0)
    motor = VibrationMotorAsync(pwm)
    try:
        print(">>> Motor running at full speed for 2 seconds")
        await motor.on_async()
        await asyncio.sleep_ms(RUN_TIME_MS)
        await motor.off_async()
        print(">>> Motor stopped")
        await run_step(motor, HALF_DUTY, "half speed")
        await run_step(motor, LOW_DUTY, "low speed")
    finally:
        try:
            await motor.aclose()
        finally:
            pwm.deinit()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())
