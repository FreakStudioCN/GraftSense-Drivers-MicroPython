# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : FDE Frost asynchronous demonstration
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin
from fde_frost_sensor_async import FDEFrostSensorAsync

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ===========================================
async def main():
    sensor = None
    uart = None
    try:
        await asyncio.sleep_ms(3000)
        print("FreakStudio: starting async driver demo")
        uart = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1)
        sensor = FDEFrostSensorAsync(1, uart)
        print("=== FDE Sensor Real-time Data ===")
        print("Temperature:", await sensor.fde_temperature_async(), "C")
        print("C1 Capacitance:", await sensor.fde_c1_async(), "pF")
        print("C2 Capacitance:", await sensor.fde_c2_async(), "pF")
        print("C3 Capacitance:", await sensor.fde_c3_async(), "pF")
        print("C2+C3 Sum:", await sensor.fde_c2_c3_sum_async(), "pF")
        print("No-load Capacitance Preset:", await sensor.fde_no_load_cap_async())
        print("Hardware Version:", await sensor.fde_hw_ver_async())
        print("Firmware Version:", await sensor.fde_fw_ver_async())
    finally:
        if sensor is not None:
            sensor.deinit()
        if uart is not None:
            deinit = getattr(uart, "deinit", None)
            if deinit is not None:
                deinit()

# ======================================== 主程序 ===============================================
asyncio.run(main())
