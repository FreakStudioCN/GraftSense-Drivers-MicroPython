"""VEML6075 asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from veml6075_async import VEML6075Async
# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDR, I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ = 0x10, 5, 4, 100000
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    if TARGET_SENSOR_ADDR not in i2c.scan():
        raise RuntimeError("VEML6075 not found")
    sensor = VEML6075Async(i2c=i2c)
    try:
        while True:
            uva, uvb, uv_index = await sensor.read_uv_async()
            print("UVA: %.2f, UVB: %.2f, UV index: %.2f" % (uva, uvb, uv_index))
            await asyncio.sleep_ms(1000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())