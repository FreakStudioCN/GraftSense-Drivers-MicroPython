# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : hogeiha
# @File    : main.py
# @Description : EWM550-7G9T10SP UWB 异步测距示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from ewm550_uwb_async import EWM550_UWBAsync

# ======================================== 全局变量 ============================================
UART_BAUDRATE = 921600
BASE_UART_ID = 1
BASE_TX_PIN = 8
BASE_RX_PIN = 9
TAG_UART_ID = 0
TAG_TX_PIN = 16
TAG_RX_PIN = 17
UART_BITS = 8
RX_TIMEOUT_MS = 600
POLL_INTERVAL_MS = 10

# ======================================== 功能函数 ============================================
async def configure(module: EWM550_UWBAsync, role: str, source_address: str, destination_address: str) -> None:
    """按来源示例配置一个 EWM550 节点并重启使配置生效。"""
    print("Enter AT mode:", await module.enter_at_mode_async())
    print("Detect module communication:", await module.check_async())
    print("Set role:", await module.set_role_async(module.Role[role]))
    print("Set source address:", await module.set_src_addr_async(source_address))
    print("Set destination address:", await module.set_dst_addr_async(destination_address))
    print("Reset and exit AT mode:", await module.reset_module_async())


async def main() -> None:
    """配置基站与标签节点，并异步轮询标签测距数据。"""
    await asyncio.sleep_ms(3000)
    base_uart = UART(BASE_UART_ID, baudrate=UART_BAUDRATE, tx=Pin(BASE_TX_PIN), rx=Pin(BASE_RX_PIN), bits=UART_BITS, parity=None, stop=1)
    tag_uart = UART(TAG_UART_ID, baudrate=UART_BAUDRATE, tx=Pin(TAG_TX_PIN), rx=Pin(TAG_RX_PIN), bits=UART_BITS, parity=None, stop=1)
    base = EWM550_UWBAsync(base_uart, rx_timeout_ms=RX_TIMEOUT_MS)
    tag = EWM550_UWBAsync(tag_uart, rx_timeout_ms=RX_TIMEOUT_MS)
    try:
        print("Enter AT mode:", await base.enter_at_mode_async())
        print("Detect module communication:", await base.check_async())
        print("Set role:", await base.set_role_async(base.Role["BASE"]))
        print("Set source address:", await base.set_src_addr_async("0000"))
        print("Set destination address:", await base.set_dst_addr_async("11110000000000000000"))
        print("Reset and exit AT mode:", await base.reset_module_async())
        print("Enter AT mode:", await tag.enter_at_mode_async())
        print("Detect module communication:", await tag.check_async())
        print("Set role:", await tag.set_role_async(tag.Role["TAG"]))
        print("Set source address:", await tag.set_src_addr_async("1111"))
        print("Set destination address:", await tag.set_dst_addr_async("00000000000000000000"))
        print("Reset and exit AT mode:", await tag.reset_module_async())
        while True:
            if tag_uart.any():
                data = tag_uart.read()
                print(await tag.parse_ranging_data_async(data))
            await asyncio.sleep_ms(POLL_INTERVAL_MS)
    finally:
        await base.aclose()
        await tag.aclose()
        base_uart.deinit()
        tag_uart.deinit()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())