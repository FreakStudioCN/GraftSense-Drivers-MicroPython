# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : lis3mdl_async.py
# @Description : LIS3MDL explicit asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from .lis3mdl import LIS3MDL
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class LIS3MDLAsync(LIS3MDL):
    """Explicit facade for bounded synchronous register transactions."""
    async def magnetic_async(self) -> tuple: return self.magnetic
    async def set_data_rate_async(self, value: int) -> None: self.data_rate = value
    async def reset_async(self) -> None: self.reset()
    async def aclose(self) -> None: self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================