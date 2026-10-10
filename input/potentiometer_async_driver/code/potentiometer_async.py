# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/15
# @Author  : 缪贵成
# @File    : potentiometer_async.py
# @Description : 异步适配的滑动变阻器驱动
# @License : MIT

# ======================================== 导入相关模块 =========================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================

ADC_MAX_VALUE = 65535

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================


class PotentiometerAsync:
    """ADC sliding potentiometer with explicit residual synchronous reads."""

    def __init__(self, adc, vref=3.3):
        if adc is None or not hasattr(adc, "read_u16"):
            raise ValueError("adc must provide read_u16")
        if vref <= 0:
            raise ValueError("vref must be positive")
        self._adc = adc
        self._vref = vref
        self._closed = False

    def read_raw(self):
        return self._adc.read_u16()

    def read_voltage(self):
        return self.read_raw() / ADC_MAX_VALUE * self._vref

    def read_ratio(self):
        raw = self.read_raw()
        min_offset = ADC_MAX_VALUE * 0.05
        max_offset = ADC_MAX_VALUE * 0.9
        raw = max(min_offset, min(raw, max_offset))
        return max(0.0, min(1.0, (raw - min_offset) / (max_offset - min_offset)))

    def get_state(self):
        raw = self.read_raw()
        return {
            "raw": raw,
            "voltage": self.read_voltage(),
            "ratio": self.read_ratio(),
        }

    async def read_raw_async(self):
        return self.read_raw()

    async def read_voltage_async(self):
        return self.read_voltage()

    async def read_ratio_async(self):
        return self.read_ratio()

    async def get_state_async(self):
        return self.get_state()

    @property
    def adc(self):
        return self._adc

    @property
    def vref(self):
        return self._vref

    def deinit(self):
        self._closed = True

    async def aclose(self):
        self.deinit()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
