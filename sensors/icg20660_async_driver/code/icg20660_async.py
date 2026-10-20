# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : icg20660_async.py
# @Description : ICG20660 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""Cooperative ICG20660 sampling while preserving source register access."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_icg20660_icg20660 import ICG20660, acc_range_sensitivity, gyro_full_scale_sensitivity


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class ICG20660Async(ICG20660):
    """ICG20660 facade that yields during the source 5 ms conversion delay."""

    CONVERSION_DELAY_MS = 5

    async def read_acceleration_async(self):
        """Read source acceleration registers, then cooperatively wait and scale."""
        raw_measurement = self._raw_accel_data
        await asyncio.sleep_ms(self.CONVERSION_DELAY_MS)
        x = raw_measurement[0] / acc_range_sensitivity[self._memory_accel_range] * 9.80665
        y = raw_measurement[1] / acc_range_sensitivity[self._memory_accel_range] * 9.80665
        z = raw_measurement[2] / acc_range_sensitivity[self._memory_accel_range] * 9.80665
        return x, y, z

    async def read_gyro_async(self):
        """Read source gyro registers, then cooperatively wait and scale."""
        raw_measurement = self._raw_gyro_data
        await asyncio.sleep_ms(self.CONVERSION_DELAY_MS)
        x = raw_measurement[0] / gyro_full_scale_sensitivity[self._memory_gyro_fs] * 0.017453293
        y = raw_measurement[1] / gyro_full_scale_sensitivity[self._memory_gyro_fs] * 0.017453293
        z = raw_measurement[2] / gyro_full_scale_sensitivity[self._memory_gyro_fs] * 0.017453293
        return x, y, z

    async def aclose(self):
        """Put the device to sleep using the source shutdown sequence."""
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
