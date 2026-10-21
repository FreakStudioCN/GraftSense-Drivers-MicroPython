# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : 缪贵成
# @File    : main.py
# @Description : AD8232 心电采集与串口协议异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from _gs_ad8232_ad8232 import AD8232
from _gs_ad8232_data_flow_processor import DataFlowProcessor
from _gs_ad8232_ecg_module_cmd import ECGModuleCMD
from _gs_ad8232_ecg_signal_processor import ECGSignalProcessor

# ======================================== 全局变量 ============================================
UART_ID = 1
UART_BAUDRATE = 115200
UART_TX_PIN = 8
UART_RX_PIN = 9
ADC_PIN = 26
LOFF_PLUS_PIN = 3
LOFF_MINUS_PIN = 4
SDN_PIN = 2
SAMPLE_RATE_HZ = 100.0

# ======================================== 功能函数 ============================================
async def main() -> None:
    """Start source-faithful sampling and protocol tasks with owned UART cleanup."""
    uart = None
    sensor = None
    processor = None
    command = None
    sample_task = None
    protocol_task = None
    try:
        await asyncio.sleep_ms(3000)
        uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
        flow = DataFlowProcessor(uart)
        sensor = AD8232(adc_pin=ADC_PIN, loff_plus_pin=LOFF_PLUS_PIN, loff_minus_pin=LOFF_MINUS_PIN, sdn_pin=SDN_PIN)
        processor = ECGSignalProcessor(ad8232=sensor, fs=SAMPLE_RATE_HZ)
        command = ECGModuleCMD(flow, sensor, processor)
        sensor.on()
        sample_task = asyncio.create_task(processor.run_async())
        protocol_task = asyncio.create_task(command.run_async())
        while True:
            await asyncio.sleep_ms(1000)
    finally:
        if processor is not None:
            processor.stop()
        if command is not None:
            command.stop()
        if sample_task is not None:
            sample_task.cancel()
        if protocol_task is not None:
            protocol_task.cancel()
        if sensor is not None:
            sensor.off()
        await asyncio.sleep_ms(0)
        if uart is not None:
            deinit = getattr(uart, "deinit", None)
            if deinit is not None:
                deinit()
# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())