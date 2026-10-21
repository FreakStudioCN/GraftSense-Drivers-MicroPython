"""PMS7003 asynchronous UART particulate-sensor demonstration."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from aqi import AQI
from machine import Pin, UART
from pms7003_async import Pms7003Async

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 16
UART_RX_PIN = 17

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = Pms7003Async(UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN)))
    try:
        await sensor.enter_passive_async()
        await sensor.wakeup_async()
        await asyncio.sleep_ms(30000)
        while True:
            data = await sensor.read_async(timeout_ms=3000)
            pm25, pm10 = data['PM2_5_ATM'], data['PM10_0_ATM']
            print('PM2.5: %s ug/m3 | PM10: %s ug/m3 | AQI: %.1f' % (pm25, pm10, AQI.aqi(pm25, pm10)))
            await asyncio.sleep_ms(2000)
    finally:
        await sensor.sleep_async()
        await sensor.aclose()

asyncio.run(main())