# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:40
# @Author  : hogeiha
# @File    : main.py
# @Description : MSE soil sensor asynchronous demonstration
# @License : MIT
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin
from mse_soil_sensor_async import MSESoilSensorAsync
# ======================================== 全局变量 ============================================
SLAVE_ADDR = 1
UART_ID = 0
TX_PIN = 16
RX_PIN = 17
# ======================================== 功能函数 ============================================
async def read_all_async(sensor: MSESoilSensorAsync) -> None:
    print("=" * 50)
    print("Sensor data (Addr: %s)" % await sensor.read_node_address_async())
    print("Temperature        : %s C" % await sensor.read_temperature_async())
    print("Capacitance        : %s pF" % await sensor.read_capacitance_async())
    print("Capacitance center : %s pF" % await sensor.read_cap_center_async())
    print("Capacitance range  : %s pF" % await sensor.read_cap_range_async())
    print("Filter count       : %s" % await sensor.read_filter_count_async())
    print("Average window     : %s" % await sensor.read_avg_window_size_async())
    print("Temp comp A        : %s" % await sensor.read_temp_comp_A_async())
    print("Temp comp B        : %s" % await sensor.read_temp_comp_B_async())
    print("Hardware version   : %s" % await sensor.read_hw_version_async())
    print("Firmware version   : %s" % await sensor.read_firmware_version_async())
    print("Device UID         : %s" % await sensor.read_device_uid_async())
    print("=" * 50)
# ======================================== 自定义类 ===========================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
async def main() -> None:
    print("FreakStudio: starting async driver demo")
    await asyncio.sleep_ms(3000)
    uart = UART(UART_ID, baudrate=9600, tx=Pin(TX_PIN), rx=Pin(RX_PIN), bits=8, parity=None, stop=1)
    sensor = MSESoilSensorAsync(SLAVE_ADDR, uart)
    try:
        await sensor.write_temp_comp_B_async(0.5)
        while True:
            await read_all_async(sensor)
            await asyncio.sleep_ms(2000)
    finally:
        await sensor.aclose()
asyncio.run(main())
