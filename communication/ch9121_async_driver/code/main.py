# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : FreakStudio
# @File    : main.py
# @Description : CH9121 TCP 客户端异步示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from machine import Pin, UART
import ch9121_safe as ch9121

# ======================================== 全局变量 ============================================
GATEWAY = (192, 168, 2, 254)
TARGET_IP = (192, 168, 2, 217)
TARGET_PORT = 2000
UART_BAUDRATE = 9600
TCP_CLIENT = 1

# ======================================== 功能函数 ============================================
async def main() -> None:
    """配置 TCP 客户端并周期性发送 UART 回环测试消息。"""
    await asyncio.sleep_ms(3000)
    eth = ch9121.CH9121Async(UART(0, baudrate=UART_BAUDRATE, tx=Pin(16), rx=Pin(17)), Pin(19, Pin.OUT))
    try:
        await eth.set_mode(TCP_CLIENT)
        await eth.set_gateway(GATEWAY)
        await eth.set_target_ip(TARGET_IP)
        await eth.set_target_port(TARGET_PORT)
        await eth.reset()
        await asyncio.sleep_ms(1000)
        count = 1
        while True:
            message = "Test message %d: Hello, UART loopback!" % count
            await eth.write_async(message.encode("utf-8"))
            try:
                print("Received:", (await eth.read_async(256, timeout_ms=100)).decode("utf-8"))
            except TimeoutError:
                print("Received: No data (check connections)")
            count += 1
            await asyncio.sleep_ms(2000)
    finally:
        await eth.aclose()

# ======================================== 自定义类 =============================================
# ======================================== 初始化配置 ==========================================
# ========================================  主程序  ============================================
asyncio.run(main())
