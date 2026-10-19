"""PMS5003T asynchronous particulate-sensor demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import UART
from _gs_pms5003t_pms5003 import PMS5003

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_TX = 16
UART_RX = 17
UART_BAUDRATE = 9600

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    uart = UART(UART_ID, tx=UART_TX, rx=UART_RX, baudrate=UART_BAUDRATE)
    pm = PMS5003(uart, lock=asyncio.Lock(), active_mode=False, interval_passive_mode=60)
    try:
        await pm.start()
        while True:
            print(pm.read())
            await asyncio.sleep_ms(1000)
    finally:
        await pm.stop()

asyncio.run(main())