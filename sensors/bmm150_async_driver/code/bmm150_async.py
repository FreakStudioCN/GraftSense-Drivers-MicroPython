# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : bmm150_async.py
# @Description : Explicit bounded-transaction BMM150 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from micropython_bmm150 import bmm150 as source

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class BMM150Async(source.BMM150):
    async def get_measurements_async(self):
        return self.measurements

    async def set_operation_mode_async(self, value):
        self.operation_mode = value

    async def get_operation_mode_async(self):
        return self.operation_mode

    async def set_data_rate_async(self, value):
        self.data_rate = value

    async def get_data_rate_async(self):
        return self.data_rate

    async def set_high_threshold_async(self, value):
        self.high_threshold = value

    async def get_high_threshold_async(self):
        return self.high_threshold

    async def set_low_threshold_async(self, value):
        self.low_threshold = value

    async def get_low_threshold_async(self):
        return self.low_threshold

    async def set_interrupt_mode_async(self, value):
        self.interrupt_mode = value

    async def get_interrupt_mode_async(self):
        return self.interrupt_mode

    async def get_status_interrupt_async(self):
        return self.status_interrupt

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================