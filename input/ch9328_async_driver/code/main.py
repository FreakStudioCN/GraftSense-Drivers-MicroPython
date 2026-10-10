"""Cooperative CH9328 keyboard demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, UART
from ch9328_async import CH9328Async

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 0
UART_RX_PIN = 1
KEYBOARD_MODE = 0

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Send a bounded Mode-0 keyboard example through the async facade."""
    await asyncio.sleep_ms(3000)
    keyboard = CH9328Async(UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN)))
    try:
        await keyboard.set_keyboard_mode_async(KEYBOARD_MODE)
        await keyboard.send_string_async("Hello")
        await keyboard.crlf_async()
        await keyboard.send_string_async("Mode0")
        if KEYBOARD_MODE == 3:
            for key_code in range(0x04, 0x66):
                await keyboard.tap_key_async(key_code)
                await asyncio.sleep_ms(50)
    finally:
        await keyboard.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())