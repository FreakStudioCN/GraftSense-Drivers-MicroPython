# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : hogeiha
# @File    : bma400_async.py
# @Description : Source-faithful BMA400 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from bma400 import BMA400, CBits, RegisterStruct

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
class SyncAdapterMixin:
    async def aclose(self):
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()


class CBitsAsync(SyncAdapterMixin, CBits):
    pass


class RegisterStructAsync(SyncAdapterMixin, RegisterStruct):
    pass


class BMA400Async(SyncAdapterMixin, BMA400):
    """Expose bounded property transactions through auditable get/set methods."""

    async def get_power_mode_async(self): return self.power_mode
    async def set_power_mode_async(self, value): self.power_mode = value
    async def get_output_data_rate_async(self): return self.output_data_rate
    async def set_output_data_rate_async(self, value): self.output_data_rate = value
    async def get_oversampling_rate_async(self): return self.oversampling_rate
    async def set_oversampling_rate_async(self, value): self.oversampling_rate = value
    async def get_acc_range_async(self): return self.acc_range
    async def set_acc_range_async(self, value): self.acc_range = value
    async def get_filter_bandwidth_async(self): return self.filter_bandwidth
    async def set_filter_bandwidth_async(self, value): self.filter_bandwidth = value
    async def get_source_data_registers_async(self): return self.source_data_registers
    async def set_source_data_registers_async(self, value): self.source_data_registers = value
    async def acceleration_async(self): return self.acceleration

    async def temperature_async(self):
        raw_temp = self._temperature
        await asyncio.sleep_ms(160)
        return (self._twos_comp(raw_temp, 8) * 0.5) + 23

# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================