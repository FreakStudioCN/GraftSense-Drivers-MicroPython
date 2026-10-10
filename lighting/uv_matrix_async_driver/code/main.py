# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 上午10:45
# @Author  : 缪贵成
# @File    : main.py
# @Description : UV matrix async demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from uv_matrix_async import UVMatrixAsync

# ======================================== 全局变量 ============================================
UV_PIN = 26
PWM_FREQ = 1000

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main() -> None:
    matrix = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: UV matrix test")
    try:
        matrix = UVMatrixAsync(pin=UV_PIN, pwm_freq=PWM_FREQ)
        await matrix.initialize_async()
        print("Status: %s" % await matrix.get_state_async())
        await matrix.on_async()
        print("UV full brightness: %s" % await matrix.get_state_async())
        await asyncio.sleep_ms(2000)
        await matrix.set_brightness_async(512)
        print("UV PWM duty=512")
        await asyncio.sleep_ms(2000)
        await matrix.off_async()
        print("UV status: %s" % await matrix.get_state_async())
        await asyncio.sleep_ms(2000)
        await matrix.toggle_async()
        print("UV toggle: %s" % await matrix.get_state_async())
        await asyncio.sleep_ms(2000)
        await matrix.toggle_async()
        print("UV toggle: %s" % await matrix.get_state_async())
    finally:
        if matrix is not None:
            await matrix.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
