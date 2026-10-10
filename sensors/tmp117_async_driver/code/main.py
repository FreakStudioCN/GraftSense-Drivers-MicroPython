"""TMP117 asynchronous demonstration for the external driver dependency."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from micropython_tmp117.tmp117 import TMP117
from tmp117_async import TMP117Async
# ======================================== 全局变量 ============================================
I2C_BUS_ID, I2C_SCL_PIN, I2C_SDA_PIN, I2C_FREQ = 0, 5, 4, 400000
TMP117_I2C_ADDR, TMP117_CHIP_ID, _TMP117_REG_WHOAMI = 0x48, 0x0117, 0x0F
PRINT_INTERVAL_MS = 2000
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# The dependency performs single bounded I2C transactions; this entry yields between samples.
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = I2C(I2C_BUS_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)
    if TMP117_I2C_ADDR not in i2c.scan():
        raise RuntimeError("TMP117 not found at 0x%02X" % TMP117_I2C_ADDR)
    raw = i2c.readfrom_mem(TMP117_I2C_ADDR, _TMP117_REG_WHOAMI, 2)
    if ((raw[0] << 8) | raw[1]) != TMP117_CHIP_ID:
        raise RuntimeError("TMP117 device ID mismatch")
    source_sensor = TMP117(i2c, address=TMP117_I2C_ADDR, debug=False,
                           wait_for_first_conversion=False)
    sensor = TMP117Async(source_sensor)
    await sensor.wait_ready_async()
    try:
        while True:
            print("Temperature: %.4f C" % await sensor.temperature_async())
            await asyncio.sleep_ms(PRINT_INTERVAL_MS)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())