# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : ben0i0d
# @File    : air530z_async.py
# @Description : Source-faithful Air530Z asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from air530z import Air530Z, NMEASender

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================
class NMEASenderAsync(NMEASender):
    async def set_baudrate_async(self, baud):
        return self.set_baudrate(baud)
    async def set_update_rate_async(self, rate):
        return self.set_update_rate(rate)
    async def set_protocol_async(self, mode):
        return self.set_protocol(mode)
    async def set_system_mode_async(self, mode):
        return self.set_system_mode(mode)
    async def set_startup_mode_async(self, mode):
        return self.set_startup_mode(mode)
    async def query_product_info_async(self):
        return self.query_product_info()

class Air530ZAsync(Air530Z):
    async def set_baudrate_async(self, baudrate):
        return self.set_baudrate(baudrate)
    async def set_update_rate_async(self, rate):
        return self.set_update_rate(rate)
    async def set_protocol_async(self, mode):
        return self.set_protocol(mode)
    async def set_system_mode_async(self, mode):
        return self.set_system_mode(mode)
    async def set_startup_mode_async(self, mode):
        return self.set_startup_mode(mode)
    async def query_product_info_async(self):
        return self.query_product_info()
    async def read_async(self):
        return self.read()
    async def aclose(self):
        await asyncio.sleep_ms(0)

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================