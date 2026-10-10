# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin
from dht11_async import DHT11Async

# ======================================== 全局变量 ============================================
MEASUREMENT_INTERVAL_MS = 2000

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = None
    pin = None
    try:
        await asyncio.sleep_ms(3000)
        pin = Pin(6, Pin.OUT, Pin.PULL_UP)
        sensor = DHT11Async(pin)
        while True:
            await sensor.measure_async()
            print("temperature: {}℃, humidity: {}%".format(
                await sensor.get_temperature_async(),
                await sensor.get_humidity_async(),
            ))
            await asyncio.sleep_ms(MEASUREMENT_INTERVAL_MS)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if pin is not None:
            deinit = getattr(pin, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())