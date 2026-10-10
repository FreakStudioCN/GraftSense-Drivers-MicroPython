"""Async TCS3472 example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from tcs3472_async import tcs3472Async

# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDRS = (0x29,)
# ======================================== 功能函数 ============================================
def recognize_color(red, green, blue):
    if red < 30 and green < 30 and blue < 30:
        return "Black"
    if red > 110 and green > 110 and blue > 110:
        return "White"
    return "Unknown"
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
    addresses = i2c.scan()
    address = next((item for item in addresses if item in TARGET_SENSOR_ADDRS), None)
    if address is None:
        raise RuntimeError("TCS3472 not found")
    sensor = tcs3472Async(i2c, address)
    try:
        while True:
            if await sensor.valid_async():
                red, green, blue = await sensor.rgb_async()
                light = await sensor.light_async()
                print("Light: %s | RGB: (%s, %s, %s) | %s" % (light, red, green, blue, recognize_color(red, green, blue)))
            await asyncio.sleep_ms(500)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())