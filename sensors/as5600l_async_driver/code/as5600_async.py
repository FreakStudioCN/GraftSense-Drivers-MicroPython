# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : hogeiha
# @File    : as5600_async.py
# @Description : AS5600L finite-register asynchronous facade
# @License : MIT
# @AsyncSafety : each API performs one finite synchronous I2C register transaction

# ======================================== 导入相关模块 =========================================
from as5600 import *

# ======================================== 全局变量 ============================================
_READ = None
REG_ZMCO = 0x00
REG_ZPOS = 0x01
REG_MPOS = 0x03
REG_MANG = 0x05
REG_CONF = 0x07
REG_RAWANGLE = 0x0C
REG_ANGLE = 0x0E
REG_AGC = 0x1A
REG_STATUS = 0x1B
REG_MAGNITUDE = 0x1C

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
_ASYNC_FACADE_P0 = True


class AS5600Async(AS5600):
    async def _field_async(self, register: int, firstbit: int, lastbit: int, value: object = _READ) -> int:
        if value is _READ:
            return self.readwrite(register, firstbit, lastbit)
        if not isinstance(value, int):
            raise ValueError("value must be int")
        return self.readwrite(register, firstbit, lastbit, value)

    async def readwrite_async(self, register: int, firstbit: int, lastbit: int, value: object = _READ) -> int:
        return await self._field_async(register, firstbit, lastbit, value)

    async def zmco_async(self) -> int: return await self._field_async(REG_ZMCO, 1, 0)
    async def zpos_async(self, value: object = _READ) -> int: return await self._field_async(REG_ZPOS, 11, 0, value)
    async def mpos_async(self, value: object = _READ) -> int: return await self._field_async(REG_MPOS, 11, 0, value)
    async def mang_async(self, value: object = _READ) -> int: return await self._field_async(REG_MANG, 11, 0, value)
    async def pm_async(self, value: object = _READ) -> int: return await self._field_async(REG_CONF, 1, 0, value)
    async def hyst_async(self, value: object = _READ) -> int: return await self._field_async(REG_CONF, 3, 2, value)
    async def outs_async(self, value: object = _READ) -> int: return await self._field_async(REG_CONF, 5, 4, value)
    async def pwmf_async(self, value: object = _READ) -> int: return await self._field_async(REG_CONF, 7, 6, value)
    async def sf_async(self, value: object = _READ) -> int: return await self._field_async(REG_CONF, 9, 8, value)
    async def fth_async(self, value: object = _READ) -> int: return await self._field_async(REG_CONF, 12, 10, value)
    async def watchdog_async(self, value: object = _READ) -> int: return await self._field_async(REG_CONF, 13, 13, value)
    async def rawangle_async(self) -> int: return await self._field_async(REG_RAWANGLE, 11, 0)
    async def angle_async(self) -> int: return await self._field_async(REG_ANGLE, 11, 0)
    async def md_async(self) -> int: return await self._field_async(REG_STATUS, 5, 5)
    async def ml_async(self) -> int: return await self._field_async(REG_STATUS, 4, 4)
    async def mh_async(self) -> int: return await self._field_async(REG_STATUS, 3, 3)
    async def agc_async(self) -> int: return await self._field_async(REG_AGC, 7, 0)
    async def magnitude_async(self) -> int: return await self._field_async(REG_MAGNITUDE, 11, 0)

    async def burn_angle_async(self) -> None: self.burn_angle()
    async def burn_setting_async(self) -> None: self.burn_setting()
    async def deinit_async(self) -> None: self.deinit()
    async def aclose(self) -> None: self.deinit()

# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
