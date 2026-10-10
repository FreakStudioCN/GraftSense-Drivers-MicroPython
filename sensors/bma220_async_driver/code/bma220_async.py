# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : jposada202020
# @File    : bma220_async.py
# @Description : BMA220 bounded asynchronous read facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from micropython_bma220.bma220 import BMA220

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================
class BMA220Async(BMA220):
    async def acceleration_async(self):
        value = self.acceleration
        await asyncio.sleep_ms(0)
        return value
    async def aclose(self):
        await asyncio.sleep_ms(0)

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================