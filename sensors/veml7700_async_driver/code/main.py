"""VEML7700 asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from veml7700_async import VEML7700Async
# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDR, I2C_SDA_PIN, I2C_SCL_PIN, I2C_FREQ = 0x10, 4, 5, 100000
INTEGRATION_TIME, SENSOR_GAIN = 100, 1 / 8
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    if TARGET_SENSOR_ADDR not in i2c.scan():
        raise RuntimeError("VEML7700 not found")
    sensor = VEML7700Async(i2c=i2c, address=TARGET_SENSOR_ADDR, it=INTEGRATION_TIME, gain=SENSOR_GAIN)
    try:
        await asyncio.sleep_ms(200)
        while True:
            print("Lux: %d lx" % await sensor.read_lux_async())
            await asyncio.sleep_ms(1000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())