# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : ben0i0d
# @File    : main.py
# @Description : HC08 蓝牙串口异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from hc08_async import HC08Async

# ======================================== 全局变量 ============================================
UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 16
UART_RX_PIN = 17
RECEIVE_TIMEOUT_MS = 200
LOOP_DELAY_MS = 50

# ======================================== 功能函数 ============================================
async def main() -> None:
    """查询 HC08 信息并回传透明串口数据。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio:HC08 test")
    module = HC08Async(UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN)))
    try:
        _, response = await module.get_name_async()
        print("hc0 Name: %s" % response)
        _, response = await module.get_version_async()
        print("hc0 Version: %s" % response)
        _, response = await module.get_role_async()
        print("hc0 Role: %s" % response)
        while True:
            ok, data = await module.recv_data_async(timeout_ms=RECEIVE_TIMEOUT_MS)
            if ok:
                print(data)
                await module.send_data_async("get data:")
                await module.send_data_async(data)
            await asyncio.sleep_ms(LOOP_DELAY_MS)
    finally:
        await module.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())