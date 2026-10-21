# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 上午11:53
# @Author  : 缪贵成
# @File    : main.py
# @Description : High-power single LED async demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from led_single_power_async import PowerLEDAsync

# ======================================== 全局变量 ============================================
LED_PIN = 14
PWM_FREQ = 1000

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main() -> None:
    led = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Test high-power LED lights")
    try:
        led = PowerLEDAsync(pin=LED_PIN, pwm_freq=PWM_FREQ)
        await led.initialize_async()
        await led.on_async()
        print("LED turned ON")
        await asyncio.sleep_ms(4000)
        await led.off_async()
        print("LED turned OFF")
        await asyncio.sleep_ms(4000)
        await led.toggle_async()
        print("LED toggled. Current state: %s" % ("ON" if await led.get_state_async() else "OFF"))
        await asyncio.sleep_ms(1000)
        for duty in range(0, 1024, 2):
            await led.set_brightness_async(duty)
            await asyncio.sleep_ms(500)
        await led.off_async()
        print("PowerLED test ended")
    finally:
        if led is not None:
            await led.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
