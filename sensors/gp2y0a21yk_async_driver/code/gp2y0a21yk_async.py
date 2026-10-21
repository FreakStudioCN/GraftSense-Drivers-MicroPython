# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : gp2y0a21yk_async.py
# @Description : Explicit bounded-transaction GP2Y0A21YK async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import gp2y0a21yk as source
from gp2y0a21yk import DISTANCE_COEFFICIENT, DISTANCE_EXPONENT, MIN_DISTANCE_CM, MAX_DISTANCE_CM

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class GP2Y0A21YKAsync(source.GP2Y0A21YK):
    async def begin_async(self, distance_pin, vcc_pin=None): return self.begin(distance_pin, vcc_pin)
    async def set_averaging_async(self, avg): return self.set_averaging(avg)
    async def set_ref_voltage_async(self, ref_v): return self.set_ref_voltage(ref_v)
    async def set_enabled_async(self, status): return self.set_enabled(status)
    async def get_distance_raw_async(self): return self.get_distance_raw()
    async def get_distance_volt_async(self) -> float:
        sum_val = 0
        for _ in range(self._average):
            sum_val += self._raw_to_millivolt(self.get_distance_raw())
            await asyncio.sleep_ms(5)
        return sum_val / self._average
    async def get_distance_centimeter_async(self) -> int:
        voltage = await self.get_distance_volt_async() / 1000
        if voltage <= 0:
            return 0
        distance = DISTANCE_COEFFICIENT * voltage ** DISTANCE_EXPONENT
        if distance < MIN_DISTANCE_CM:
            return MIN_DISTANCE_CM
        if distance > MAX_DISTANCE_CM:
            return MAX_DISTANCE_CM
        return int(distance + 0.5)
    async def is_closer_async(self, threshold: float) -> bool:
        if not isinstance(threshold, (int, float)):
            raise TypeError('threshold must be a number, got %s' % type(threshold))
        return await self.get_distance_centimeter_async() < threshold
    async def is_farther_async(self, threshold: float) -> bool:
        if not isinstance(threshold, (int, float)):
            raise TypeError('threshold must be a number, got %s' % type(threshold))
        return await self.get_distance_centimeter_async() > threshold
    async def deinit_async(self): return self.deinit()
    async def aclose(self): return self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================