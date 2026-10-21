# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : icm20948_async.py
# @Description : ICM20948 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""Cooperative lifecycle wrapper for the ICM20948 source driver."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class ICM20948Async:
    """Serialize bounded I2C reads for an already constructed source sensor."""

    SETTLE_DELAY_MS = 1000

    def __init__(self, sensor):
        self._sensor = sensor
        self._lock = asyncio.Lock()
        self._closed = False

    @classmethod
    async def from_sensor_async(cls, sensor):
        """Yield during the source one-second settle interval after construction."""
        await asyncio.sleep_ms(cls.SETTLE_DELAY_MS)
        return cls(sensor)

    async def read_acceleration_async(self):
        """Read the source acceleration property under the adapter lock."""
        async with self._lock:
            return self._sensor.acceleration

    async def read_gyro_async(self):
        """Read the source gyro property under the adapter lock."""
        async with self._lock:
            return self._sensor.gyro

    async def read_temperature_async(self):
        """Read the source temperature property under the adapter lock."""
        async with self._lock:
            return self._sensor.temperature

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
