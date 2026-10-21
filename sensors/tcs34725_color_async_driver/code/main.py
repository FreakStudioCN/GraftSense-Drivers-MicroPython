try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from tcs34725_color import html_hex, html_rgb
from tcs34725_color_async import TCS34725Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    sensor = TCS34725Async(I2C(0, scl=Pin(5), sda=Pin(4), freq=100000), 0x29)
    try:
        await sensor.active_async(True, Pin(2, Pin.OUT))
        print(await sensor.sensor_id_async())
        await sensor.integration_time_async(24.0)
        await sensor.gain_async(4)
        await sensor.threshold_async(cycles=5, min_value=100, max_value=2000)
        while True:
            raw = await sensor.read_async(raw=True)
            print(html_rgb(raw), html_hex(raw))
            await asyncio.sleep_ms(3000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())