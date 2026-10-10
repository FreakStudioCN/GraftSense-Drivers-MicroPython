# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/25 下午6:46
# @Author  : 李清水
# @File    : main.py
# @Description : DS1232 watchdog async demonstration
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import Pin, Timer
from ds1232_async import DS1232Async

# ======================================== 全局变量 ============================================
WDI_PIN = 7
RST_PIN = 6
FEED_INTERVAL_MS = 300
STOP_FEED_DELAY_MS = 10000
system_reset_flag = False
stop_feed_requested = False

# ======================================== 功能函数 ============================================
def rst_callback(pin) -> None:
    global system_reset_flag
    system_reset_flag = True


def stop_feed_callback(timer) -> None:
    """IRQ-safe one-shot callback; task context performs the I/O stop."""
    global stop_feed_requested
    stop_feed_requested = True


# ======================================== 自定义类 ============================================
# ======================================== 初始化配置 ==========================================
async def main() -> None:
    global system_reset_flag, stop_feed_requested
    watchdog = None
    reset_pin = None
    stop_timer = None
    await asyncio.sleep_ms(3000)
    print("FreakStudio: DS1232 Watchdog Test Program")
    try:
        watchdog = DS1232Async(wdi_pin=WDI_PIN, feed_interval=FEED_INTERVAL_MS)
        await watchdog.initialize_async()
        await watchdog.kick_async()
        reset_pin = Pin(RST_PIN, Pin.IN, Pin.PULL_UP)
        reset_pin.irq(trigger=Pin.IRQ_FALLING, handler=rst_callback)
        stop_timer = Timer(0)
        stop_timer.init(
            mode=Timer.ONE_SHOT,
            period=STOP_FEED_DELAY_MS,
            callback=stop_feed_callback,
        )
        while True:
            if stop_feed_requested:
                stop_feed_requested = False
                print("Stopping watchdog feed")
                await watchdog.stop_async()
            if system_reset_flag:
                print("DS1232 reset pin triggered")
                break
            print("System running... Time: %d ms" % time.ticks_ms())
            await asyncio.sleep_ms(1000)
    finally:
        if stop_timer is not None:
            stop_timer.deinit()
        if reset_pin is not None:
            reset_pin.irq(handler=None)
        if watchdog is not None:
            await watchdog.aclose()


# ======================================== 主程序 ============================================
if __name__ == "__main__":
    asyncio.run(main())
