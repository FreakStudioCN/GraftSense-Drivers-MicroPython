# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : lis2mdl_async.py
# @Description : LIS2MDL explicit asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from .lis2mdl import LIS2MDL
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class LIS2MDLAsync(LIS2MDL):
    """Explicit facade for bounded synchronous register transactions."""
    async def magnetic_async(self) -> tuple: return self.magnetic
    async def set_data_rate_async(self, value: int) -> None: self.data_rate = value
    async def reset_async(self) -> None: self.reset()
    async def aclose(self) -> None:
        """The source owns no resources to release; the caller owns the bus."""
        return None
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
