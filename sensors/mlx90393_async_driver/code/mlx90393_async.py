# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Adafruit
# @File    : mlx90393_async.py
# @Description : MLX90393 协作单次磁场测量
# @License : MIT

"""Async MLX90393 single-shot measurement with cooperative conversion wait."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from micropython_mlx90393.mlx90393 import MLX90393

# ======================================== 全局变量 ============================================
CMD_SM = 0b00110000
CMD_RM = 0b01000000
CMD_AXIS_ALL = 0x0E

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class MLX90393Async(MLX90393):
    async def read_magnetic_async(self):
        # Keep the source conversion margin, but never round it down.
        delay_ms = max(1, int(self._TCONV[self._c_df][self._c_osr] * 1.1 + 0.999))
        self._i2c.writeto(self._address, bytes([CMD_SM | CMD_AXIS_ALL]))
        self._status_last = self._i2c.readfrom(self._address, 1)[0]
        await asyncio.sleep_ms(delay_ms)
        self._i2c.writeto(self._address, bytes([CMD_RM | CMD_AXIS_ALL]))
        data = self._i2c.readfrom(self._address, 7)
        self._status_last = data[0]
        hall = self._hallconf_index
        return (
            self._unpack_axis_data(self._c_rx, data[1:3]) * self._resolutionsxy[self._c_rx][hall][self._c_gain],
            self._unpack_axis_data(self._c_ry, data[3:5]) * self._resolutionsxy[self._c_ry][hall][self._c_gain],
            self._unpack_axis_data(self._c_rz, data[5:7]) * self._resolutionsz[self._c_rz][hall][self._c_gain],
        )
    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================
