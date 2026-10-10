"""VCNL4010 asynchronous demonstration."""
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from vcnl4010_async import VCNL4010Async
# ======================================== 全局变量 ============================================
_DEVICE_I2C_ADDR, _DEVICE_ID_REG, _EXPECTED_DEVICE_ID = 0x13, 0x81, 0x21
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    await asyncio.sleep_ms(3000)
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
    if _DEVICE_I2C_ADDR not in i2c.scan():
        raise RuntimeError("VCNL4010 not found")
    sensor = VCNL4010Async(i2c)
    try:
        if i2c.readfrom_mem(_DEVICE_I2C_ADDR, _DEVICE_ID_REG, 1)[0] != _EXPECTED_DEVICE_ID:
            raise RuntimeError("VCNL4010 device ID mismatch")
        while True:
            print("Proximity: %d, Ambient: %.2f lux" % (await sensor.proximity_async(), await sensor.ambient_async()))
            await asyncio.sleep_ms(2000)
    finally:
        await sensor.aclose()
# ======================================== 主程序 ================================================
if __name__ == "__main__":
    asyncio.run(main())