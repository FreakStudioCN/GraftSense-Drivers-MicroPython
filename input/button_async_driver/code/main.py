"""Cooperative touch-key demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from touchkey_async import TouchKeyAsync

# ======================================== 全局变量 ============================================
BUTTON_PIN = 6
DEBOUNCE_MS = 50

# ======================================== 功能函数 ============================================
def on_press():
    print("Button pressed")


def on_release():
    print("Button released")


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Poll the interrupt-backed key without blocking other tasks."""
    await asyncio.sleep_ms(3000)
    button = TouchKeyAsync(BUTTON_PIN, TouchKeyAsync.high, DEBOUNCE_MS, on_press, on_release)
    button.start()
    try:
        while True:
            state = button.get_state()
            print("Current button state:", "Pressed" if state else "Released")
            await asyncio.sleep_ms(500)
    finally:
        await button.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())