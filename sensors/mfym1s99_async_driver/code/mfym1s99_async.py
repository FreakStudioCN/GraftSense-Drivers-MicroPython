# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : December
# @File    : mfym1s99_async.py
# @Description : MFYM-1S-9-9 协作 UART 采样接口
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from mfym1s99 import MFYM1S99, _MAX_LINE_BYTES, _TRIMMED_BUFFER_BYTES, _validate_positive_int, _validate_non_negative_int, _validate_number

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class MFYM1S99Async(MFYM1S99):
    def __init__(self, uart, value_key="s", value_index=MFYM1S99.DEFAULT_VALUE_INDEX,
                 timeout_ms=MFYM1S99.DEFAULT_TIMEOUT_MS, sensitivity=0.36,
                 polarity=1, debug=False):
        super().__init__(uart, value_key, value_index, timeout_ms, sensitivity, polarity, debug)
        self._reader_lock = asyncio.Lock()
    async def aclose(self): self.deinit()
    async def parse_line_async(self, data): return self.parse_line(data)
    async def field_async(self, sample, name, default=None): return self.field(sample, name, default)
    async def temperature_c_async(self, sample): return self.temperature_c(sample)

    async def clear_async(self, max_wait_ms=50):
        _validate_positive_int(max_wait_ms, "max_wait_ms")
        self._ensure_active()
        self._rx_buffer = b""
        deadline = time.ticks_add(time.ticks_ms(), max_wait_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            remaining = time.ticks_diff(deadline, time.ticks_ms())
            line = await self.read_raw_line_async(max(1, remaining))
            if line is None:
                self._rx_buffer = b""
                return
            await asyncio.sleep_ms(0)
    async def read_raw_line_async(self, timeout_ms=None):
        timeout = self._timeout_ms if timeout_ms is None else timeout_ms
        _validate_positive_int(timeout, "timeout_ms")
        async with self._reader_lock:
            self._ensure_active(); deadline = time.ticks_add(time.ticks_ms(), timeout)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                newline = self._rx_buffer.find(b"\n")
                if newline >= 0:
                    line = self._rx_buffer[:newline + 1]
                    self._rx_buffer = self._rx_buffer[newline + 1:]
                    return line
                available = self._uart.any()
                if available:
                    chunk = self._uart.read(available)
                    if chunk:
                        self._rx_buffer += chunk
                        if len(self._rx_buffer) > _MAX_LINE_BYTES:
                            self._rx_buffer = self._rx_buffer[-_TRIMMED_BUFFER_BYTES:]
                await asyncio.sleep_ms(1)
        return None
    async def read_sample_async(self, timeout_ms=None):
        timeout = self._timeout_ms if timeout_ms is None else timeout_ms
        _validate_positive_int(timeout, "timeout_ms"); deadline = time.ticks_add(time.ticks_ms(), timeout)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            sample = await self.read_raw_line_async(time.ticks_diff(deadline, time.ticks_ms()))
            if sample is None: return None
            parsed = self.parse_line(sample)
            if parsed is not None and parsed["values"]: return parsed
        return None

    async def sample_value_async(self, sample): return self.sample_value(sample)
    async def read_raw_value_async(self, timeout_ms=None):
        sample = await self.read_sample_async(timeout_ms)
        return None if sample is None else self.sample_value(sample)

    async def average_raw_async(self, samples=20, interval_ms=10):
        _validate_positive_int(samples, "samples"); _validate_non_negative_int(interval_ms, "interval_ms")
        values = []
        for _ in range(samples * 3):
            value = await self.read_raw_value_async()
            if value is not None: values.append(value)
            if len(values) == samples: return sum(values) / samples
            await asyncio.sleep_ms(interval_ms)
        raise RuntimeError("UART timeout: received %d of %d samples" % (len(values), samples))

    async def zero_async(self, samples=MFYM1S99.DEFAULT_ZERO_SAMPLES, discard=MFYM1S99.DEFAULT_DISCARD_SAMPLES, interval_ms=10, max_spread_ratio=0.10):
        _validate_positive_int(samples, "samples")
        if samples < 3:
            raise ValueError("samples must be at least 3")
        _validate_non_negative_int(discard, "discard")
        _validate_non_negative_int(interval_ms, "interval_ms")
        spread_limit = _validate_number(max_spread_ratio, "max_spread_ratio")
        if spread_limit <= 0:
            raise ValueError("max_spread_ratio must be greater than zero")

        discarded = 0
        attempts = 0
        while discarded < discard and attempts < max(1, discard * 3):
            attempts += 1
            if await self.read_raw_value_async() is not None:
                discarded += 1
            await asyncio.sleep_ms(0)
        if discarded != discard:
            raise RuntimeError("UART timeout while discarding startup samples")

        values = []
        attempts = 0
        while len(values) < samples and attempts < samples * 3:
            attempts += 1
            value = await self.read_raw_value_async()
            if value is not None:
                values.append(value)
            await asyncio.sleep_ms(interval_ms)
        if len(values) != samples:
            raise RuntimeError("UART timeout: received %d of %d zero samples" % (len(values), samples))

        values.sort()
        middle = samples // 2
        if samples & 1:
            baseline = values[middle]
        else:
            baseline = (values[middle - 1] + values[middle]) / 2.0
        if baseline == 0:
            raise ValueError("zero reading is 0; use two-point calibration")
        spread_ratio = (values[-1] - values[0]) / abs(baseline)
        if spread_ratio > spread_limit:
            raise ValueError("unstable zero: min=%.1f max=%.1f; keep sensor unloaded" % (values[0], values[-1]))
        self._zero_raw = baseline
        self._linear_slope = None
        self._linear_offset = None
        self._log("zero baseline=%.3f" % baseline)
        return self._zero_raw

    async def set_two_point_calibration_async(self, raw1, pressure1_kpa, raw2, pressure2_kpa): return self.set_two_point_calibration(raw1, pressure1_kpa, raw2, pressure2_kpa)
    async def pressure_from_raw_async(self, raw): return self.pressure_from_raw(raw)
    async def read_pressure_kpa_async(self, timeout_ms=None):
        value = await self.read_raw_value_async(timeout_ms)
        return None if value is None else self.pressure_from_raw(value)
    async def get_zero_raw_async(self): return self.get_zero_raw()
    async def get_sensitivity_async(self): return self.get_sensitivity()
    async def set_sensitivity_async(self, sensitivity): return self.set_sensitivity(sensitivity)
    async def deinit_async(self): return self.deinit()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ================================================