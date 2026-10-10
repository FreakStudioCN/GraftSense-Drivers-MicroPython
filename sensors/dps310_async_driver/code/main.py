# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, SoftI2C
from dps310_async import DPS310Async

TARGET_DPS310_ADDRS = [0x76, 0x77]


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
async def main():
    i2c_bus = None
    sensor = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: DPS310 Pressure Sensor I2C Auto Scan and Read")
    try:
        i2c_bus = SoftI2C(sda=Pin(4), scl=Pin(5), freq=100_000)
        devices_list = i2c_bus.scan()
        print("START I2C SCANNER")
        if not devices_list:
            raise SystemExit("I2C scan found no devices, program exited")
        for device in devices_list:
            if device in TARGET_DPS310_ADDRS:
                sensor = DPS310Async(i2c=i2c_bus, address=device)
                break
        if sensor is None:
            raise RuntimeError("No target sensor device found in I2C bus")
        while True:
            print("Pressure: %sHPa" % await sensor.get_pressure_async())
            await asyncio.sleep_ms(1000)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c_bus is not None:
            deinit = getattr(i2c_bus, "deinit", None)
            if deinit is not None:
                deinit()
asyncio.run(main())