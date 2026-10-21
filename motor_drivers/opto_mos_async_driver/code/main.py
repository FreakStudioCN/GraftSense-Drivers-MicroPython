# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : main.py
# @Description : 光耦 MOS PWM 异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, PWM
from opto_mos_simple_async import OptoMosSimpleAsync

# ======================================== 全局变量 ============================================
PWM_PIN = 6
INVERTED_PWM_PIN = 16
PWM_FREQ = 1000
FIRST_DELAY_MS = 5000
SECOND_DELAY_MS = 10000

# ======================================== 功能函数 ============================================
async def main() -> None:
    """执行来源示例的常规和反相 PWM 光耦 MOS 测试。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    pwm = PWM(Pin(PWM_PIN))
    pwm.freq(PWM_FREQ)
    driver = OptoMosSimpleAsync(pwm)
    try:
        await driver.init_async()
        for duty in (10000, 70000):
            await driver.set_duty_async(duty)
            print("Status:", await driver.get_status_async())
        for percent in (25.0, 150.0):
            await driver.set_percent_async(percent)
            print("Status:", await driver.get_status_async())
        await driver.full_on_async()
        await asyncio.sleep_ms(FIRST_DELAY_MS)
        await driver.off_async()
        await asyncio.sleep_ms(SECOND_DELAY_MS)
        inverted_pwm = PWM(Pin(INVERTED_PWM_PIN))
        inverted_pwm.freq(PWM_FREQ)
        inverted = OptoMosSimpleAsync(inverted_pwm, inverted=True)
        try:
            await inverted.init_async()
            await inverted.set_percent_async(30.0)
            print("Inverted 30% ->", await inverted.get_status_async())
            await inverted.full_on_async()
            await inverted.off_async()
        finally:
            await inverted.aclose()
    finally:
        await driver.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())