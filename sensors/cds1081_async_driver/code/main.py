# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:30
# @Author  : hogeiha
# @File    : main.py
# @Description : CDS1081 asynchronous demonstration
# @License : MIT
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART, Pin
from cds1081_async import CDS1081Async
# ======================================== 全局变量 ============================================
SLAVE_ADDR = 1
UART_ID = 0
TX_PIN = 16
RX_PIN = 17
# ======================================== 功能函数 ============================================
async def main() -> None:
    uart = None
    sensor = None
    print("FreakStudio: starting async driver demo")
    await asyncio.sleep_ms(3000)
    try:
        uart = UART(UART_ID, baudrate=9600, tx=Pin(TX_PIN), rx=Pin(RX_PIN), bits=8, parity=None, stop=1)
        sensor = CDS1081Async(slave_addr=SLAVE_ADDR, uart=uart)
        await sensor.set_calibration_async(6000)
        await sensor.set_alarm_threshold_async(40000)
        await sensor.set_clear_threshold_async(20000)
        while True:
            print("Node address:", await sensor.get_node_address_async())
            print("Rain status:", await sensor.get_rain_status_async())
            print("Temperature:", await sensor.get_temperature_async(), "C")
            print("Capacitance:", await sensor.get_capacitance_async(), "pF")
            print("Count0 value:", await sensor.get_count0_async())
            print("Calibration ideal value:", await sensor.get_calibration_value_async(), "pF")
            print("Alarm threshold:", await sensor.get_alarm_threshold_async())
            print("Clear threshold:", await sensor.get_clear_threshold_async())
            await asyncio.sleep_ms(1000)
    finally:
        if sensor is not None:
            sensor.deinit()
        if uart is not None:
            close_uart = getattr(uart, "deinit", None)
            if close_uart is not None:
                close_uart()
# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ===========================================
asyncio.run(main())
