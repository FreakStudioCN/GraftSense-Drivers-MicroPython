# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : kx132_async.py
# @Description : KX132 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from .kx132 import KX132, NORMAL_MODE, STANDBY_MODE
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class KX132Async(KX132):
    async def acceleration_async(self): return self.acceleration
    async def soft_reset_async(self):
        self._operating_mode = STANDBY_MODE; self._soft_reset = 1
        await asyncio.sleep_ms(50)
        self._operating_mode = NORMAL_MODE
    async def aclose(self):
        deinit=getattr(self,'deinit',None)
        if deinit is not None: deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================