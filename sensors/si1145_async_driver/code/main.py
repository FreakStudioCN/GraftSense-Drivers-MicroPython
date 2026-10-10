try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from si1145_async import SI1145Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100000)
    sensor = SI1145Async(i2c=i2c, addr=0x60)
    try:
        await sensor._reset_async()
        await sensor._load_calibration_async()
        await sensor._write8_async(0x18, 0x00)
        while True:
            print(await sensor.read_uv_async())
            await asyncio.sleep_ms(2000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == '__main__':
    asyncio.run(main())