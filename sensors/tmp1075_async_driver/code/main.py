"""TMP1075 asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import I2C, Pin
from tmp1075_async import TMP1075Async
# ======================================== 全局变量 ============================================
I2C_ID, SDA_PIN, SCL_PIN, I2C_FREQ = 0, 4, 5, 400000
TMP1075_ADDRESS, EXPECTED_DEVICE_ID, PRINT_INTERVAL_MS = 0x48, 0x7500, 1000
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = I2C(I2C_ID, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
    if TMP1075_ADDRESS not in i2c.scan():
        raise RuntimeError("TMP1075 not found at 0x%02X" % TMP1075_ADDRESS)
    sensor = TMP1075Async(i2c, address=TMP1075_ADDRESS, check=False)
    try:
        if await sensor.device_id_async() != EXPECTED_DEVICE_ID:
            raise RuntimeError("TMP1075 device ID mismatch")
        while True:
            print("Temperature: %.4f C / %.4f F" % (await sensor.temperature_c_async(), await sensor.temperature_f_async()))
            await asyncio.sleep_ms(PRINT_INTERVAL_MS)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())