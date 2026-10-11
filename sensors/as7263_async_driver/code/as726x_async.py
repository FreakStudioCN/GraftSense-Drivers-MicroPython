# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Roberto Colistete Jr.
# @File    : as726x_async.py
# @Description : AS726x asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from as726x import *

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True
MEASUREMENT_TIMEOUT_MS = 1000
POLLING_DELAY_MS = 5

def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.monotonic() * 1000)

def _ticks_diff(end, start):
    return time.ticks_diff(end, start) if hasattr(time, "ticks_diff") else end - start
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
class AS726XAsync(AS726X):
    async def take_one_shot_sync_measurement(self, timeout_ms=MEASUREMENT_TIMEOUT_MS):
        self.clear_data_available()
        self.take_one_shot_async_measurement()
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while not self.data_available():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("Timeout waiting for AS726X measurement")
            await asyncio.sleep_ms(POLLING_DELAY_MS)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit:
            deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
