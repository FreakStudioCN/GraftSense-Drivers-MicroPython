# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : 缪贵成
# @File    : guva_s12sd_async.py
# @Description : Cooperative averaged-sampling GUVA-S12SD async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import guva_s12sd as source

# ======================================== 全局变量 ============================================
_SAMPLE_COUNT = 10
_SAMPLE_INTERVAL_MS = 5

# ======================================== 功能函数 ============================================
def _to_uvi(voltage):
    millivolts = voltage * 1000
    thresholds = (227, 318, 408, 503, 606, 696, 795, 881, 976, 1079, 1170)
    for index, threshold in enumerate(thresholds):
        if millivolts < threshold:
            return index
    return 11

# ======================================== 自定义类 ============================================
class GUVA_S12SDAsync(source.GUVA_S12SD):
    async def read_async(self):
        total = 0
        for index in range(_SAMPLE_COUNT):
            total += self._adc.read_u16()
            if index + 1 < _SAMPLE_COUNT:
                await asyncio.sleep_ms(_SAMPLE_INTERVAL_MS)
        return (total / _SAMPLE_COUNT / 65535) * 3.3

    async def get_uv_index_async(self):
        return _to_uvi(await self.read_async())

    async def voltage_async(self):
        return await self.read_async()

    async def uvi_async(self):
        return await self.get_uv_index_async()

    async def aclose(self):
        return None

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================