# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : robert-hh
# @File    : hx711_gpio_async.py
# @Description : Cooperative asynchronous HX711 load-cell driver
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from machine import disable_irq, enable_irq

# ======================================== 全局变量 ============================================
_MIN_SAMPLE_INTERVAL_MS = 100

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class HX711Async:
    """Async coordinator for the source HX711 GPIO protocol.

    The 24-bit pulse train remains synchronous because its microsecond timing
    must not be interrupted.  Data-ready waiting and repeated sampling are
    cooperative and bounded by an explicit timeout.
    """

    def __init__(self, clock, data, gain=128, min_interval_ms=_MIN_SAMPLE_INTERVAL_MS):
        if clock is None or not hasattr(clock, "value"):
            raise ValueError("clock must provide value")
        if data is None or not hasattr(data, "value"):
            raise ValueError("data must provide value")
        if gain not in (128, 64, 32):
            raise ValueError("gain must be 128, 64 or 32")
        if not isinstance(min_interval_ms, int) or min_interval_ms < 0:
            raise ValueError("min_interval_ms must be a non-negative int")
        self._clock = clock
        self._data = data
        self._gain = self._gain_code(gain)
        self._offset = 0
        self._scale = 1.0
        self._time_constant = 0.25
        self._filtered = 0.0
        self._min_interval_ms = min_interval_ms
        self._next_sample_ms = time.ticks_ms()
        self._lock = asyncio.Lock()
        self._closed = False
        self._clock.value(0)

    @staticmethod
    def _gain_code(gain):
        if gain == 128:
            return 1
        if gain == 64:
            return 3
        return 2

    async def _wait_for_slot_async(self):
        while time.ticks_diff(self._next_sample_ms, time.ticks_ms()) > 0:
            await asyncio.sleep_ms(5)

    async def _wait_ready_async(self, timeout_ms):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while self._data.value():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("HX711 data-ready timeout")
            await asyncio.sleep_ms(5)

    def _read_ready_sync(self):
        result = 0
        for _ in range(24 + self._gain):
            state = disable_irq()
            try:
                self._clock.value(1)
                self._clock.value(0)
            finally:
                enable_irq(state)
            result = (result << 1) | self._data.value()
        result >>= self._gain
        if result > 0x7FFFFF:
            result -= 0x1000000
        return result

    async def read_async(self, timeout_ms=1000):
        if self._closed:
            raise RuntimeError("HX711 is closed")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        async with self._lock:
            await self._wait_for_slot_async()
            await self._wait_ready_async(timeout_ms)
            value = self._read_ready_sync()
            self._next_sample_ms = time.ticks_add(time.ticks_ms(), self._min_interval_ms)
            return value

    async def read_average_async(self, times=3, timeout_ms=1000):
        if not isinstance(times, int) or times <= 0:
            raise ValueError("times must be a positive int")
        total = 0
        for _ in range(times):
            total += await self.read_async(timeout_ms)
        return total / times

    async def read_lowpass_async(self, timeout_ms=1000):
        value = await self.read_async(timeout_ms)
        self._filtered += self._time_constant * (value - self._filtered)
        return self._filtered

    async def get_value_async(self, timeout_ms=1000):
        return await self.read_lowpass_async(timeout_ms) - self._offset

    async def get_units_async(self, timeout_ms=1000):
        return (await self.get_value_async(timeout_ms)) / self._scale

    async def tare_async(self, times=15, timeout_ms=1000):
        self._offset = await self.read_average_async(times, timeout_ms)

    async def set_gain_async(self, gain, timeout_ms=1000):
        self._gain = self._gain_code(gain)
        self._filtered = await self.read_async(timeout_ms)

    def set_scale(self, scale):
        if not isinstance(scale, (int, float)) or scale == 0:
            raise ValueError("scale must be a non-zero number")
        self._scale = scale

    def set_offset(self, offset):
        if not isinstance(offset, (int, float)):
            raise ValueError("offset must be a number")
        self._offset = offset

    def set_time_constant(self, time_constant=None):
        if time_constant is None:
            return self._time_constant
        if not isinstance(time_constant, (int, float)) or not 0 < time_constant < 1:
            raise ValueError("time_constant must be between 0 and 1")
        self._time_constant = time_constant

    def power_down(self):
        self._clock.value(0)
        self._clock.value(1)

    def power_up(self):
        self._clock.value(0)

    async def aclose(self):
        if not self._closed:
            self.power_down()
            self._closed = True

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ============================================
