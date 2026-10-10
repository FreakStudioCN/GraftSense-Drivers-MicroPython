# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : isl29125_async.py
# @Description : ISL29125 explicit asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from .isl29125 import ISL29125
# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class ISL29125Async(ISL29125):
    """Explicit facade for bounded synchronous register transactions."""
    async def configure_async(self, operation_mode: int, sensing_range: int, adc_resolution: int) -> None:
        self.operation_mode = operation_mode
        self.sensing_range = sensing_range
        self.adc_resolution = adc_resolution
        self.clear_register_flag()
    async def colors_async(self) -> tuple: return self.colors
    async def device_id_async(self) -> int: return self._device_id
    async def aclose(self) -> None: self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================