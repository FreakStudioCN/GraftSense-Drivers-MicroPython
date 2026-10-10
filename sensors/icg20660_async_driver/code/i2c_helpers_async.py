# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : i2c_helpers_async.py
# @Description : ICG20660 asynchronous I2C helper facades
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from i2c_helpers import CBits, RegisterStruct

# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()


class CBitsAsync(SyncAdapterMixin, CBits):
    """Async facade; each delegated call remains a short sync transaction."""

    pass


class RegisterStructAsync(SyncAdapterMixin, RegisterStruct):
    """Async facade; each delegated call remains a short sync transaction."""

    pass


# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================