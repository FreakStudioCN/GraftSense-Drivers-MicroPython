"""Cooperative SIM800 identity-query demonstration."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, UART
from sim800_async import SIM800SMSAsync

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 16
UART_RX_PIN = 17

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main():
    """Read basic SIM800 information without blocking the event loop."""
    await asyncio.sleep_ms(3000)
    device = SIM800SMSAsync(UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN)))
    try:
        await device.initialize_async()
        print(await device.get_phone_number_async())
        print(await device.get_manufacturer_async())
        print(await device.get_signal_quality_async())
        print(await device.get_serial_number_async())
    finally:
        await device.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
