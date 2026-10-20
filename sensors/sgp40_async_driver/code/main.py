"""SGP40 asynchronous sensor demonstration."""
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : Roman Shevchik, async adaptation by GraftSense
# @File    : main.py
# @Description : Async SGP40 and SGP41 demonstration
# @License : MIT

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import Pin, SoftI2C
from _gs_sgp40_sensor_pack_2.bus_service import I2cAdapter
from sgp4x_async import SGP4XAsync

TARGET_SENSOR_ADDRS = [0x59]
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
SENSOR_ID = 0


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
async def main():
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    i2c_bus = SoftI2C(sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=I2C_FREQ)
    devices_list = i2c_bus.scan()
    if not devices_list or TARGET_SENSOR_ADDRS[0] not in devices_list:
        raise RuntimeError("No target sensor found on I2C bus")
    sensor = SGP4XAsync(I2cAdapter(i2c_bus), address=TARGET_SENSOR_ADDRS[0], sensor_id=SENSOR_ID)
    try:
        sn = await sensor.get_id_async()
        print("Serial number: 0x%04X 0x%04X 0x%04X" % sn)
        result = await sensor.execute_self_test_async()
        print("Self test: %s (0x%04X)" % ("PASS" if result == 0xD400 else "FAIL", result))
        if SENSOR_ID == 1:
            for _ in range(10):
                value = await sensor.execute_conditioning_async(50, 25)
                print("Conditioning VOC raw: %d" % value.VOC)
                await asyncio.sleep_ms(1000)
        while True:
            value = await sensor.measure_raw_signal_async(50, 25)
            print("VOC raw: %d" % value.VOC)
            if SENSOR_ID == 1:
                print("NOx raw: %d" % value.NOx)
            await asyncio.sleep_ms(1000)
    finally:
        await sensor.aclose()


asyncio.run(main())
