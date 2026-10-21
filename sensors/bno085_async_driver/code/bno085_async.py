# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : rdagger
# @File    : bno085_async.py
# @Description : Cooperative UART-RVC BNO085 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import bno085 as source
BNO085TimeoutError = source.BNO085TimeoutError
__version__ = source.__version__

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class BNO085Async(source.BNO085):
    async def heading_async(self):
        start = source._ticks_ms()
        timeout_ms = int(self._timeout * 1000)
        while source._ticks_diff(source._ticks_ms(), start) < timeout_ms:
            header = await self._read_exact_async(2, start, timeout_ms)
            if header != bytes((self.FRAME_HEADER, self.FRAME_HEADER)):
                continue
            payload = await self._read_exact_async(self.FRAME_PAYLOAD_LEN, start, timeout_ms)
            result = self._parse_frame(payload)
            if result is not None:
                return result
        raise source.BNO085TimeoutError("Unable to read RVC heading message within timeout")

    async def _read_exact_async(self, size, start, timeout_ms):
        data = bytearray()
        while len(data) < size:
            if source._ticks_diff(source._ticks_ms(), start) >= timeout_ms:
                raise source.BNO085TimeoutError("UART read timed out")
            chunk = self._uart.read(size - len(data))
            if chunk:
                data.extend(chunk)
            else:
                await asyncio.sleep_ms(1)
        return bytes(data)

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================