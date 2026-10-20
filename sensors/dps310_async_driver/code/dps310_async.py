# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Adafruit Industries
# @File    : dps310_async.py
# @Description : Explicit bounded-transaction DPS310 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
from micropython_dps310 import dps310 as source

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class DPS310Async(source.DPS310):
    async def get_pressure_async(self): return self.pressure
    async def get_altitude_async(self): return self.altitude
    async def get_temperature_async(self): return self.temperature
    async def get_sea_level_pressure_async(self): return self.sea_level_pressure
    async def set_pressure_oversample_async(self, value): self.pressure_oversample = value
    async def set_pressure_rate_async(self, value): self.pressure_rate = value
    async def set_temperature_oversample_async(self, value): self.temperature_oversample = value
    async def set_temperature_rate_async(self, value): self.temperature_rate = value
    async def set_mode_async(self, value): self.mode = value
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None: deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
