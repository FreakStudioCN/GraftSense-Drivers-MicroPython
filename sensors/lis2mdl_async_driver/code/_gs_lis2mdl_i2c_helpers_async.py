# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : i2c_helpers_async.py
# @Description : lis2mdl asynchronous I2C helper facades
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from _gs_lis2mdl_micropython_lis2mdl.i2c_helpers import CBits, RegisterStruct
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SyncAdapterMixin:
    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None: deinit()
class CBitsAsync(SyncAdapterMixin, CBits): pass
class RegisterStructAsync(SyncAdapterMixin, RegisterStruct): pass
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================