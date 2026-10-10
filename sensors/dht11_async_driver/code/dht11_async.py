# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : 李清水
# @File    : dht11_async.py
# @Description : DHT11 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""DHT11 async entry points with an explicit strict-timing limitation."""
from dht11 import DHT11, InvalidChecksum, InvalidPulseCount


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class DHT11Async(DHT11):
    """DHT11 facade; waveform capture is intentionally marked non-cooperative."""

    NOT_ASYNC_SAFE = True

    async def measure_async(self):
        """Run the source waveform transaction; it blocks for its required timing window."""
        self.measure()

    async def aclose(self):
        """Release only driver state; the caller retains ownership of its GPIO."""
        self._temperature = -1
        self._humidity = -1
    async def get_humidity_async(self):
        """Return the humidity produced by the preceding measurement."""
        return self._humidity

    async def get_temperature_async(self):
        """Return the temperature produced by the preceding measurement."""
        return self._temperature


__all__ = ("DHT11Async", "InvalidChecksum", "InvalidPulseCount")

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
