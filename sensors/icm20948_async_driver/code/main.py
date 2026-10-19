# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import I2C, Pin
from _gs_icm20948_micropython_icm20948 import ICM20948
from icm20948_async import ICM20948Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    i2c = None
    icm = None
    adapter = None
    try:
        await asyncio.sleep_ms(3000)
        i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
        if 0x68 not in i2c.scan():
            raise RuntimeError("ICM20948 not found")
        icm = ICM20948(i2c, address=0x68, debug=False)
        adapter = await ICM20948Async.from_sensor_async(icm)
        print(await adapter.read_acceleration_async(), await adapter.read_gyro_async(), await adapter.read_temperature_async())
    finally:
        if icm is not None:
            try:
                icm.deinit()
            except Exception as error:
                print("Sensor cleanup failed: %s" % error)
        if i2c is not None:
            deinit = getattr(i2c, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())