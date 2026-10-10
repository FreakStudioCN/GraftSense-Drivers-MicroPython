# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @File    : main.py
# @Description : CCS811 asynchronous example with owned-bus cleanup
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import I2C, Pin
from ccs811_async import CCS811Async

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main() -> None:
    sensor = None
    i2c_bus = None
    try:
        await asyncio.sleep_ms(3000)
        i2c_bus = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
        devices_list = i2c_bus.scan()
        if not devices_list:
            raise RuntimeError("I2C scan found no devices")
        for device in devices_list:
            if device in (0x5A, 0x5B):
                sensor = CCS811Async(i2c=i2c_bus, addr=device)
                break
        if sensor is None:
            raise RuntimeError("No target sensor device found in I2C bus")
        await sensor.setup_async()
        await asyncio.sleep_ms(2000)
        print("APP validity: %s" % await sensor.app_valid_async())
        print("Sensor error status: %s" % await sensor.check_for_error_async())
        print("Sensor baseline value: 0x%04X" % await sensor.get_base_line_async())
        await sensor.set_drive_mode_async(1)
        for index in range(5):
            co2 = await sensor.read_eCO2_async()
            tvoc = await sensor.read_tVOC_async()
            print("Reading %d - eCO2: %d ppm, TVOC: %d ppb" % (index + 1, co2, tvoc))
            await asyncio.sleep_ms(2000)
        await sensor.reset_async()
        await asyncio.sleep_ms(2000)
    finally:
        if sensor is not None:
            await sensor.aclose()
        if i2c_bus is not None and hasattr(i2c_bus, "deinit"):
            i2c_bus.deinit()

# ======================================== 主程序 ==============================================
if __name__ == "__main__":
    asyncio.run(main())