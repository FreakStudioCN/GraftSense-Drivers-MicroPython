"""TMP102 asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from tmp102_async import Tmp102Async
import alert
import conversionrate
import extendedmode
import shutdown
import oneshot
from convertors import Fahrenheit, Kelvin
# ======================================== 全局变量 ============================================
_TMP102_ADDR = 0x48
_PRINT_INTERVAL_MS = 2000
# ======================================== 功能函数 ============================================
# Extension imports above register the optional TMP102 APIs on the base class.
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
    if _TMP102_ADDR not in i2c.scan():
        raise RuntimeError("TMP102 not found at 0x%02X" % _TMP102_ADDR)
    sensor = Tmp102Async(i2c, _TMP102_ADDR)
    last_print = time.ticks_ms()
    try:
        while True:
            now = time.ticks_ms()
            if time.ticks_diff(now, last_print) >= _PRINT_INTERVAL_MS:
                temperature = await sensor.temperature_async()
                print("Temperature: %.4f C / %.4f F / %.2f K" % (temperature, Fahrenheit().convert_to(temperature), Kelvin().convert_to(temperature)))
                last_print = now
            await asyncio.sleep_ms(50)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())