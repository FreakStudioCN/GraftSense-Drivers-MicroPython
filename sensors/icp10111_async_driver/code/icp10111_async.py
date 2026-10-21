# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : icp10111_async.py
# @Description : ICP10111 asynchronous measurement facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from icp10111 import ICP10111
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class ICP10111Async(ICP10111):
    async def measurements_async(self, timeout_ms=200):
        started = time.ticks_ms(); data = bytearray(9)
        self._i2c.writeto(self._address, bytes([0xC7]), False)
        self._i2c.writeto(self._address, self._mode.to_bytes(2, "big"), False)
        await asyncio.sleep_ms(30)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms: raise RuntimeError("ICP10111 measurement timeout")
        self._i2c.readfrom_into(self._address, data, False)
        press_raw = data[0] << 16 | data[1] << 8 | data[3]; temp_raw = data[6] << 8 | data[7]
        return self.get_pressure(press_raw, temp_raw), -45 + (175 / 2**16.0 * temp_raw)
    async def reset_async(self):
        self._i2c.writeto(self._address, bytes([0x80, 0x5D]), False); await asyncio.sleep_ms(100)
    async def aclose(self):
        deinit=getattr(self,'deinit',None)
        if deinit is not None: deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
