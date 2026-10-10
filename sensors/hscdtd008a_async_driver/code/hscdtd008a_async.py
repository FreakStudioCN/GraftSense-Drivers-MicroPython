# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 12:00
# @Author  : goctaprog@gmail.com
# @File    : hscdtd008a_async.py
# @Description : Async HSCDTD008A adapter
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import hscdtd008a

# ======================================== 全局变量 ============================================
CONVERSION_TIME_MS = 5

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class HSCDTD008AAsync:
    """HSCDTD008A 的协作式异步适配器。"""

    def __init__(self, adapter, debug=False):
        if adapter is None or not hasattr(adapter, "read_buf_from_mem"):
            raise ValueError("adapter must provide read_buf_from_mem")
        self._sensor = hscdtd008a.HSCDTD008A(adapter, debug=debug)
        self._lock = asyncio.Lock()
        self._closed = False

    @property
    def offset_drift_values(self):
        return self._sensor.offset_drift_values

    async def get_id_async(self):
        async with self._lock:
            return self._sensor.get_id()

    async def get_status_async(self):
        async with self._lock:
            return self._sensor.get_status()

    async def enable_temp_meas_async(self, enable=True):
        async with self._lock:
            self._sensor.enable_temp_meas(enable)
        await asyncio.sleep_ms(CONVERSION_TIME_MS)

    async def get_temperature_async(self):
        async with self._lock:
            return self._sensor.get_temperature()

    async def start_measure_async(self, continuous_mode=True, update_rate=1, active_pwr_mode=True):
        async with self._lock:
            self._sensor.start_measure(continuous_mode, update_rate, active_pwr_mode)
        if active_pwr_mode and not continuous_mode:
            await asyncio.sleep_ms(CONVERSION_TIME_MS)

    async def get_axis_async(self, axis=-1):
        async with self._lock:
            return self._sensor.get_axis(axis)

    async def perform_self_test_async(self):
        async with self._lock:
            return self._sensor.perform_self_test()

    async def set_use_offset_async(self, enabled):
        async with self._lock:
            self._sensor.use_offset = bool(enabled)

    async def aclose(self):
        if not self._closed:
            async with self._lock:
                self._sensor.deinit()
                self._closed = True

    def deinit(self):
        if not self._closed:
            self._sensor.deinit()
            self._closed = True

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
