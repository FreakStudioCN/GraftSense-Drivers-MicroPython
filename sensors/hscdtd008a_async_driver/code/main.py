# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 12:00
# @Author  : goctaprog@gmail.com
# @File    : main.py
# @Description : Async HSCDTD008A demo
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import math
from machine import Pin, SoftI2C
from _gs_hscdtd008a_sensor_pack.bus_service import I2cAdapter
from hscdtd008a_async import HSCDTD008AAsync

# ======================================== 全局变量 ============================================
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000
TARGET_SENSOR_ADDR = 0x0C
EXPECTED_CHIP_ID = 0x49
MEAS_DELAY_MS = 250

# ======================================== 功能函数 ============================================
async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    devices = i2c_bus.scan()
    if TARGET_SENSOR_ADDR not in devices:
        raise RuntimeError("target sensor not found on I2C bus")
    sensor = HSCDTD008AAsync(I2cAdapter(i2c_bus))
    try:
        if await sensor.get_id_async() != EXPECTED_CHIP_ID:
            raise RuntimeError("chip ID mismatch")
        await sensor.start_measure_async(active_pwr_mode=True)
        if not await sensor.perform_self_test_async():
            raise RuntimeError("sensor self-test failed")
        await sensor.enable_temp_meas_async(True)
        status = await sensor.get_status_async()
        if status[3]:
            print("Sensor temperature: %d C" % await sensor.get_temperature_async())
        await sensor.start_measure_async(continuous_mode=False)
        await asyncio.sleep_ms(MEAS_DELAY_MS)
        status = await sensor.get_status_async()
        if status[0] or status[1]:
            print("magnetic field: %s" % (await sensor.get_axis_async(-1),))
        await sensor.set_use_offset_async(True)
        await sensor.start_measure_async(continuous_mode=True)
        await asyncio.sleep_ms(MEAS_DELAY_MS)
        status = await sensor.get_status_async()
        if status[0]:
            field = await sensor.get_axis_async(-1)
            print("magnetic field strength: %.2f" % math.sqrt(field[0] ** 2 + field[1] ** 2 + field[2] ** 2))
    finally:
        await sensor.aclose()

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
asyncio.run(main())
