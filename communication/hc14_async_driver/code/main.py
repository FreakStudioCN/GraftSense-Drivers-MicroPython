# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/18
# @Author  : FreakStudio
# @File    : main.py
# @Description : HC14 LoRa 异步通信示例
# @License : MIT

# ======================================== 导入相关模块 =========================================
from machine import UART, Pin
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import urandom
import time
from hc14_lora_async import HC14_LoraAsync

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
async def main() -> None:
    channel, power, rate = 7, 20, 7
    reply = bytes([urandom.getrandbits(8) for _ in range(80)])
    await asyncio.sleep_ms(3000)
    print("FreakStudio: HC14_Lora Test Start")
    hc0 = HC14_LoraAsync(UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17)))
    hc1 = HC14_LoraAsync(UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9)))
    try:
        await hc0.start(); await hc1.start()
        ok, response = await hc0.test_comm_async()
        print("[OK] AT communication normal:" if ok else "[ERR] AT communication failed", response)
        if ok:
            await hc0.set_channel_async(channel); await hc0.set_rate_async(rate); await hc0.set_power_async(power)
            print("Firmware version:", await hc0.get_version_async())
            print("Current parameters:", await hc0.get_params_async())
        ok, response = await hc1.test_comm_async()
        print("[OK] AT communication normal:" if ok else "[ERR] AT communication failed", response)
        if ok:
            await hc1.set_channel_async(channel); await hc1.set_rate_async(rate); await hc1.set_power_async(power)
            print("Firmware version:", await hc1.get_version_async())
            print("Current parameters:", await hc1.get_params_async())
        await asyncio.sleep_ms(2000)
        print("Entering transparent mode, waiting for data...")
        print("Sent:", reply, await hc1.transparent_send_async(reply))
        started = time.ticks_ms()
        while True:
            ok, response = await hc0.transparent_recv_async()
            if ok:
                try: message = response.decode("utf-8")
                except UnicodeError: message = str(response)
                print("Received:", message)
                print("Elapsed time: %d ms" % time.ticks_diff(time.ticks_ms(), started))
    finally:
        await hc0.aclose(); await hc1.aclose()

asyncio.run(main())
