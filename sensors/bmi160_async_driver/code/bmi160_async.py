# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : bmi160_async.py
# @Description : Cooperative BMI160 lifecycle facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import bmi160 as source

# ======================================== 全局变量
ACCEL_RANGE_2G = source.ACCEL_RANGE_2G
ACCEL_RANGE_4G = source.ACCEL_RANGE_4G
ACCEL_RANGE_8G = source.ACCEL_RANGE_8G
ACCEL_RANGE_16G = source.ACCEL_RANGE_16G
AVERAGING = source.AVERAGING
BANDWIDTH_25 = source.BANDWIDTH_25
BANDWIDTH_50 = source.BANDWIDTH_50
BANDWIDTH_100 = source.BANDWIDTH_100
BANDWIDTH_400 = source.BANDWIDTH_400
FILTER = source.FILTER
GYRO_NORMAL = source.GYRO_NORMAL
GYRO_OSR2 = source.GYRO_OSR2
GYRO_OSR4 = source.GYRO_OSR4
GYRO_RANGE_125 = source.GYRO_RANGE_125
GYRO_RANGE_250 = source.GYRO_RANGE_250
GYRO_RANGE_500 = source.GYRO_RANGE_500
GYRO_RANGE_1000 = source.GYRO_RANGE_1000
GYRO_RANGE_2000 = source.GYRO_RANGE_2000
NO_UNDERSAMPLE = source.NO_UNDERSAMPLE
UNDERSAMPLE = source.UNDERSAMPLE


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class BMI160(source.BMI160):
    """BMI160 facade with cooperative reset, power-up and shutdown delays."""

    async def initialize_async(self):
        self._soft_reset = source.RESET_COMMAND
        await asyncio.sleep_ms(15)
        self._read = 0x03
        await asyncio.sleep_ms(100)
        self._read = source.ACC_POWER_NORMAL
        await asyncio.sleep_ms(100)
        self._read = source.GYRO_POWER_NORMAL
        await asyncio.sleep_ms(100)
        self._initialized = True

    async def soft_reset_async(self):
        self._soft_reset = source.RESET_COMMAND
        await asyncio.sleep_ms(15)
        self._initialized = False

    async def deinit_async(self):
        if self._i2c is None:
            return
        self._read = source.ACC_POWER_SUSPEND
        await asyncio.sleep_ms(100)
        self._read = source.GYRO_POWER_SUSPEND
        await asyncio.sleep_ms(100)
        self._initialized = False

    async def aclose(self):
        await self.deinit_async()

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================