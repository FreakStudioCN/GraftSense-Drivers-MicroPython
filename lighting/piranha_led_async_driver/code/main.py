# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 零高幸
# @File    : main.py
# @Description : Piranha LED 异步演示
# @License : MIT

# ======================================== 导入相关模块 =========================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from piranha_led import POLARITY_ANODE, POLARITY_CATHODE
from piranha_led_async import PiranhaLEDAsync

# ======================================== 全局变量 ============================================

LED_PIN = 6
TEST_COUNT = 3
BLINK_INTERVAL_MS = 1000
IS_ANODE = False

# ======================================== 功能函数 ============================================


async def main() -> None:
    """运行来源示例对应的异步 LED 演示。\n\nRun the asynchronous LED demo mapped from the source example."""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: Running Piranha LED async demo")
    polarity = POLARITY_ANODE if IS_ANODE else POLARITY_CATHODE
    led = PiranhaLEDAsync(pin_number=LED_PIN, polarity=polarity)
    try:
        for _ in range(TEST_COUNT):
            await led.on_async()
            await asyncio.sleep_ms(BLINK_INTERVAL_MS)
            await led.off_async()
            await asyncio.sleep_ms(BLINK_INTERVAL_MS)
        await led.toggle_async()
        await asyncio.sleep_ms(BLINK_INTERVAL_MS)
        await led.toggle_async()
        await asyncio.sleep_ms(BLINK_INTERVAL_MS)
    finally:
        await led.off_async()
        await led.aclose()


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================

asyncio.run(main())