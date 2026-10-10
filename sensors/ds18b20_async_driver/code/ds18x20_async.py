# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Damien P. George
# @File    : ds18x20_async.py
# @Description : Cooperative DS18X20 conversion facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from ds18x20 import DS18X20

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


 # ======================================== 自定义类 ============================================
class DS18X20Async(DS18X20):
    """Cooperative high-level conversion wrapper.

    OneWire reset, bit slots and scratchpad transfers deliberately remain
    synchronous strict-timing primitives from the source library.
    """

    def scan(self):
        return super().scan()

    def read_temp(self, rom):
        return super().read_temp(rom)

    async def convert_temp_async(self, rom=None, conversion_ms=500):
        if not isinstance(conversion_ms, int) or conversion_ms < 0:
            raise ValueError("conversion_ms must be a non-negative integer")
        self.convert_temp(rom)
        await asyncio.sleep_ms(conversion_ms)

    async def aclose(self):
        if self.powerpin is not None:
            self.powerpin(DS18X20.PULLUP_OFF)
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ==============================================