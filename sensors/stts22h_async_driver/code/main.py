"""Async STTS22H temperature example."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from stts22h_async import STTS22HAsync

# ======================================== 全局变量 ============================================
ADDRESS = 0x3C
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
    if ADDRESS not in i2c.scan():
        raise RuntimeError("STTS22H not found")
    sensor = STTS22HAsync(i2c, address=ADDRESS)
    try:
        while True:
            print("Temperature: %.2f C" % await sensor.temperature_async())
            await asyncio.sleep_ms(1000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())