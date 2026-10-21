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
import as726x as _source
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._async_lock = asyncio.Lock()

    async def _wait_status_async(self, mask, value, deadline):
        while True:
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("Timeout waiting for AS726X measurement")
            status = _source._read_physical_register(self._i2c, self._addr, AS726X_SLAVE_STATUS_REG)
            if status & mask == value:
                return status
            await asyncio.sleep_ms(min(POLLING_DELAY_MS, max(0, time.ticks_diff(deadline, time.ticks_ms()))))

    async def _virtual_read_async(self, register, deadline):
        status = _source._read_physical_register(self._i2c, self._addr, AS726X_SLAVE_STATUS_REG)
        if status & 0x01:
            _source._read_physical_register(self._i2c, self._addr, AS726X_SLAVE_READ_REG)
        await self._wait_status_async(0x02, 0, deadline)
        _source._write_physical_register(self._i2c, self._addr, AS726X_SLAVE_WRITE_REG, register)
        await self._wait_status_async(0x01, 0x01, deadline)
        return _source._read_physical_register(self._i2c, self._addr, AS726X_SLAVE_READ_REG)

    async def _virtual_write_async(self, register, value, deadline):
        await self._wait_status_async(0x02, 0, deadline)
        _source._write_physical_register(self._i2c, self._addr, AS726X_SLAVE_WRITE_REG, register | 0x80)
        await self._wait_status_async(0x02, 0, deadline)
        _source._write_physical_register(self._i2c, self._addr, AS726X_SLAVE_WRITE_REG, value)

    async def take_one_shot_sync_measurement(self, timeout_ms=MEASUREMENT_TIMEOUT_MS):
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")
        async with self._async_lock:
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            reg = await self._virtual_read_async(AS726X_CONTROL_SETUP, deadline)
            await self._virtual_write_async(AS726X_CONTROL_SETUP, reg & 0b11111101, deadline)
            reg = await self._virtual_read_async(AS726X_CONTROL_SETUP, deadline)
            await self._virtual_write_async(AS726X_CONTROL_SETUP, (reg & 0b11110011) | (AS726X_ONE_SHOT_READING_ALL_CHANNELS << 2), deadline)
            while not (await self._virtual_read_async(AS726X_CONTROL_SETUP, deadline)) & 0x02:
                await asyncio.sleep_ms(POLLING_DELAY_MS)

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit:
            deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
