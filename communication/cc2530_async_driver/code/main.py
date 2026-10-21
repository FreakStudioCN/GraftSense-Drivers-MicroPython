# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : FreakStudio
# @File    : main.py
# @Description : CC253x 双节点 UART 异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
from cc253x_ttl_async import CC253xTTLAsync

# ======================================== 全局变量 ============================================
UART_BAUDRATE = 9600
COORDINATOR_UART = 0
NODE_UART = 1

# ======================================== 功能函数 ============================================
async def main() -> None:
    """执行来源示例的 PANID、信道和透明传输命令序列。"""
    await asyncio.sleep_ms(3000)
    print("FreakStudio: CC253x single-reader async demo")
    coordinator = CC253xTTLAsync(UART(COORDINATOR_UART, baudrate=UART_BAUDRATE, tx=Pin(16), rx=Pin(17)))
    node = CC253xTTLAsync(UART(NODE_UART, baudrate=UART_BAUDRATE, tx=Pin(8), rx=Pin(9)))
    try:
        panid, channel = await coordinator.read_panid_channel_async()
        await node.set_panid_async(int(panid, 16))
        await node.set_channel_async(int(channel, 16))
        await node.set_custom_short_addr_async(0xFFFF)
        await coordinator.send_coord_to_node_async(0xFFFF, "coord_to_node")
        await node.send_node_to_coord_async("node_to_coord")
        await node.send_node_to_node_async(0xAAFF, 0xFFAA, "node_to_node")
        await coordinator.send_transparent_async(b"Here is transparent")
        print("Frame:", await node.recv_frame_async())
        await coordinator.read_status_async()
        await node.read_status_async()
    finally:
        await coordinator.aclose()
        await node.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())