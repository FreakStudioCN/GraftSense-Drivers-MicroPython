# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C
from ahtx0_async import AHT20Async

I2C_ID = 1
INTERVAL_MS = 2500


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
async def main():
    sensor = None
    await asyncio.sleep_ms(3000)
    i2c = None
    try:
        i2c = I2C(I2C_ID)
        sensor = AHT20Async(i2c)
        await sensor.initialize_async()
        print("AHT20 sensor test started")
        while True:
            try:
                temp, humi = await sensor.measure_async()
                print("Temperature : %5.1f C" % temp)
                print("  Humidity  : %5.1f %%rH" % humi)
                print("-" * 28)
            except RuntimeError as error:
                print("Sensor runtime error: %s" % error)
            except OSError as error:
                print("Sensor OS error: %s" % error)
            await asyncio.sleep_ms(INTERVAL_MS)
    finally:
        if sensor is not None:
            await sensor.aclose()


# ======================================== 主程序 ==============================================
if __name__ == "__main__":
    asyncio.run(main())