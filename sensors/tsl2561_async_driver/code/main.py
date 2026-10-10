"""TSL2561 asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from tsl2561 import T_SLOW
from tsl2561_async import TSL2561Async
# ======================================== 全局变量 ============================================
TARGET_SENSOR_ADDRS = (0x29, 0x39, 0x49)
I2C_SDA_PIN, I2C_SCL_PIN, I2C_FREQ = 4, 5, 100000
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    address = next((item for item in i2c.scan() if item in TARGET_SENSOR_ADDRS), None)
    if address is None:
        raise RuntimeError("TSL2561 not found")
    sensor = TSL2561Async(i2c, addr=address)
    try:
        await sensor.set_power_up_async(True)
        await sensor.set_timing_gain_async(T_SLOW, gain=False)
        print("TSL2561 ID: %s" % await sensor.get_id_async())
        print("Raw channels: %s" % (await sensor.read_raw_async(),))
        while True:
            print("Lux: %.2f" % await sensor.get_lumi_async())
            await asyncio.sleep_ms(1000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())