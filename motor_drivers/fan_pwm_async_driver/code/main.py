# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : main.py
# @Description : PWM 风扇异步演示
# @License : MIT

# ======================================== 导入相关模块 =========================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from fan_pwm_async import FanPWMAsync

# ======================================== 全局变量 ============================================

FAN_PIN = 6
DUTY_STEPS = (256, 512, 768, 1023)
STEP_DELAY_MS = 5000

# ======================================== 功能函数 ============================================


async def main() -> None:
    """运行来源示例对应的 PWM 风扇异步演示。\n\nRun the asynchronous PWM fan demo mapped from the source example."""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Starting PWM fan async demo")
    fan = FanPWMAsync(pin=FAN_PIN)
    try:
        await fan.on_async()
        print("Current duty: %s" % await fan.get_speed_async())
        await asyncio.sleep_ms(STEP_DELAY_MS)
        await fan.off_async()
        print("Current duty: %s" % await fan.get_speed_async())
        await asyncio.sleep_ms(STEP_DELAY_MS)
        for duty in DUTY_STEPS:
            await fan.set_speed_async(duty)
            print("Current duty: %s" % await fan.get_speed_async())
            await asyncio.sleep_ms(STEP_DELAY_MS)
    finally:
        await fan.aclose()


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

asyncio.run(main())