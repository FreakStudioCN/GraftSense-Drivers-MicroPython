# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : FreakStudio
# @File    : main.py
# @Description : PN532 UART 异步读卡示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from pn532 import MIFARE_CMD_AUTH_A
from pn532_uart_async import PN532_UARTAsync

# ======================================== 全局变量 ============================================
UART_ID = 1
UART_BAUDRATE = 115200
UART_TX_PIN = 8
UART_RX_PIN = 9
MIFARE_BLOCK = 4
DEFAULT_KEY = b"\xff\xff\xff\xff\xff\xff"

# ======================================== 功能函数 ============================================
async def main() -> None:
    """读取 MIFARE 卡块并保留来源示例的写入测试。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: starting async driver demo")
    nfc = PN532_UARTAsync(UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN)), reset=None, debug=True)
    try:
        print("Firmware:", await nfc.firmware_version_async())
        await nfc.SAM_configuration_async()
        uid = await nfc.read_passive_target_async(timeout_ms=1000)
        if uid and await nfc.mifare_classic_authenticate_block_async(uid, MIFARE_BLOCK, MIFARE_CMD_AUTH_A, DEFAULT_KEY):
            print(await nfc.mifare_classic_read_block_async(MIFARE_BLOCK))
            await nfc.mifare_classic_write_block_async(MIFARE_BLOCK, b"\x01" * 16)
        await nfc.power_down_async()
        await nfc.reset_async()
    finally:
        await nfc.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())