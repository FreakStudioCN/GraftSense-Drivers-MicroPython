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
try:
    from time import ticks_ms, ticks_diff
except ImportError:
    import time
    ticks_ms = lambda: int(time.monotonic() * 1000)
    ticks_diff = lambda end, start: end - start
from as726x import *

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
class AS726XAsync(AS726X):
    async def take_one_shot_sync_measurement(self, timeout_ms=_MEASUREMENT_TIMEOUT_MS):
        self.clear_data_available()
        self.take_one_shot_async_measurement()
        started = ticks_ms()
        while not self.data_available():
            if ticks_diff(ticks_ms(), started) > timeout_ms:
                raise RuntimeError("Timeout waiting for AS726X measurement")
            await asyncio.sleep_ms(_POLLING_DELAY)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit:
            deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
