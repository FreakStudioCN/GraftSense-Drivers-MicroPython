# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Sebastian Plamauer
# @File    : bmx055_async.py
# @Description : Cooperative BMX055 composite async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from _gs_bmx055_bma2x2 import BMA2X2
from _gs_bmx055_bmg160 import BMG160
from _gs_bmx055_bmm050 import BMM050

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class BMX055Async:
    def __init__(self, i2c, accel_addr=24, gyro_addr=104, mag_addr=16):
        if i2c is None:
            raise ValueError("i2c must not be None")
        self._i2c = i2c
        self._accel_addr = accel_addr
        self._gyro_addr = gyro_addr
        self._mag_addr = mag_addr
        self.accel = None
        self.gyro = None
        self.mag = None

    async def initialize_async(self):
        try:
            self.accel = BMA2X2(self._i2c, self._accel_addr, defer_compensation=True)
            await self.accel.compensation_async()
            self.gyro = BMG160(self._i2c, self._gyro_addr, defer_compensation=True)
            await self.gyro.compensation_async()
            self.mag = BMM050(self._i2c, self._mag_addr, defer_initialization=True)
            await asyncio.sleep_ms(3)
            self.mag.finish_initialization()
        except Exception:
            await self.aclose()
            raise
        return self

    async def get_xyz_async(self):
        return (self.accel.xyz(), self.gyro.xyz(), self.mag.xyz())

    async def aclose(self):
        for sensor in (self.accel, self.gyro, self.mag):
            if sensor is not None:
                sensor.deinit()
        self.accel = None
        self.gyro = None
        self.mag = None
        self._i2c = None

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================