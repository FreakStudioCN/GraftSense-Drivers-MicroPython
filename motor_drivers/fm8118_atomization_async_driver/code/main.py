# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : main.py
# @Description : FM8118 雾化模块异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from fm8118_atomization_async import FM8118_AtomizationAsync

# ======================================== 全局变量 ============================================
ATOMIZER_PIN = 6
STEP_DELAY_MS = 10000

# ======================================== 功能函数 ============================================
async def main() -> None:
    """持续执行来源示例中的开启、关闭和切换测试。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio:Testing the FM8118-based atomization module")
    atomizer = FM8118_AtomizationAsync(pin=ATOMIZER_PIN)
    try:
        while True:
            print("turn on")
            await atomizer.on_async()
            print("status:", await atomizer.is_on_async())
            await asyncio.sleep_ms(STEP_DELAY_MS)
            print("turn off...")
            await atomizer.off_async()
            print("status:", await atomizer.is_on_async())
            await asyncio.sleep_ms(STEP_DELAY_MS)
            print("toggle...")
            await atomizer.toggle_async()
            print("status:", await atomizer.is_on_async())
            await asyncio.sleep_ms(STEP_DELAY_MS)
    except KeyboardInterrupt:
        print("test stop")
    finally:
        await atomizer.off_async()
        await atomizer.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())