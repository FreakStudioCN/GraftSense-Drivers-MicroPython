"""VL53L1X asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from vl53l1x_async import VL53L1XAsync
# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDRS = (0x29,)
I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ = 5, 4, 400000
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = None
    await asyncio.sleep_ms(3000)
    try:
        i2c = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
        address = next((item for item in i2c.scan() if item in TARGET_SENSOR_ADDRS), None)
        if address is None:
            raise RuntimeError("VL53L1X not found")
        sensor = VL53L1XAsync(i2c=i2c, address=address)
        await sensor.initialize_async()
        while True:
            print("Range: %d mm" % await sensor.read_async())
            await asyncio.sleep_ms(50)
    finally:
        if sensor is not None:
            await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())