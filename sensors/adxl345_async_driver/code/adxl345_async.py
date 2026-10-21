# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : fanday
# @File    : adxl345_async.py
# @Description : Source-faithful asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""ADXL345 async initialization with injected bus ownership."""

# Preserve the documented exception contract on MicroPython.
try:
    TimeoutError
except NameError:
    try:
        from uasyncio import TimeoutError
    except ImportError:
        from asyncio import TimeoutError

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
try:
    from time import ticks_ms, ticks_diff, ticks_add
except ImportError:
    import time
    ticks_ms = lambda: int(time.monotonic() * 1000)
    ticks_diff = lambda end, start: end - start
    ticks_add = lambda base, delta: base + delta

from _gs_adxl345_adxl345 import adxl345, DATA_FORMAT, BW_RATE, INT_ENABLE, OFSX, OFSY, OFSZ, POWER_CTL


# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class adxl345Async(adxl345):
    def __init__(self, i2c, cs):
        if i2c is None or cs is None:
            raise ValueError("i2c and cs cannot be None")
        self.i2c = i2c
        self.cs = cs
        self.slvAddr = None

    @staticmethod
    def _remaining(deadline):
        return ticks_diff(deadline, ticks_ms())

    async def _wait_until_ready(self, deadline):
        remaining = self._remaining(deadline)
        if remaining < 1000:
            raise TimeoutError("ADXL345 initialization deadline expired")
        await asyncio.sleep_ms(1000)
        if self._remaining(deadline) < 0:
            raise TimeoutError("ADXL345 initialization deadline expired")

    async def initialize_async(self, timeout_ms=2500):
        if timeout_ms < 0:
            raise ValueError("timeout_ms must be non-negative")
        deadline = ticks_add(ticks_ms(), timeout_ms)
        self.cs.value(1)
        await self._wait_until_ready(deadline)
        for address in self.i2c.scan():
            if self._remaining(deadline) < 0:
                raise TimeoutError("ADXL345 scan timeout")
            if self.i2c.readfrom_mem(address, 0, 1)[0] == 0xE5:
                self.slvAddr = address
                break
        if self.slvAddr is None:
            raise OSError("ADXL345 not found")
        for register, value in ((DATA_FORMAT, 0x2B), (BW_RATE, 0x0A),
                                (INT_ENABLE, 0x00), (OFSX, 0x00),
                                (OFSY, 0x00), (OFSZ, 0x00), (POWER_CTL, 0x28)):
            if self._remaining(deadline) < 0:
                raise TimeoutError("ADXL345 configuration timeout")
            self.writeByte(register, value)
        await self._wait_until_ready(deadline)

    async def readXYZ_async(self):
        return super().readXYZ()

    async def writeByte_async(self, addr, data):
        return super().writeByte(addr, data)

    async def readByte_async(self, addr):
        return super().readByte(addr)

    async def aclose(self):
        self.slvAddr = None
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
