# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : adt7410_async.py
# @Description : ADT7410 cooperative property facade
# @License : MIT
# @AsyncSafety : source 240ms operation-mode settling is cooperative here

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from adt7410 import *

# ======================================== 全局变量 ============================================
_RESET_WAIT_MS = 1
_MODE_WAIT_MS = 240

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
_ASYNC_FACADE_P0 = True


class ADT7410Async(ADT7410):
    async def deinit_async(self) -> None:
        self.deinit()

    async def aclose(self) -> None:
        await self.deinit_async()

    async def reset_async(self) -> None:
        try:
            self._i2c.writeto(self._address, bytes([_REG_RESET]))
        except OSError as error:
            raise RuntimeError("I2C write failed during ADT7410 reset") from error
        await asyncio.sleep_ms(_RESET_WAIT_MS)

    async def temperature_async(self) -> float:
        return ADT7410.temperature.fget(self)

    async def get_operation_mode_async(self) -> str:
        return ADT7410.operation_mode.fget(self)

    async def set_operation_mode_async(self, value: int) -> None:
        if not isinstance(value, int) or value not in _OPERATION_MODE_VALUES:
            raise ValueError("operation_mode must be a valid ADT7410 mode")
        self._operation_mode = value
        await asyncio.sleep_ms(_MODE_WAIT_MS)

    async def get_resolution_mode_async(self) -> str:
        return ADT7410.resolution_mode.fget(self)

    async def set_resolution_mode_async(self, value: int) -> None:
        ADT7410.resolution_mode.fset(self, value)

    async def get_comparator_mode_async(self) -> str:
        return ADT7410.comparator_mode.fget(self)

    async def set_comparator_mode_async(self, value: int) -> None:
        ADT7410.comparator_mode.fset(self, value)

    async def alert_status_async(self) -> object:
        return ADT7410.alert_status.fget(self)

    async def get_high_temperature_async(self) -> int:
        return ADT7410.high_temperature.fget(self)

    async def set_high_temperature_async(self, value: int) -> None:
        ADT7410.high_temperature.fset(self, value)

    async def get_low_temperature_async(self) -> int:
        return ADT7410.low_temperature.fget(self)

    async def set_low_temperature_async(self, value: int) -> None:
        ADT7410.low_temperature.fset(self, value)

    async def get_critical_temperature_async(self) -> int:
        return ADT7410.critical_temperature.fget(self)

    async def set_critical_temperature_async(self, value: int) -> None:
        ADT7410.critical_temperature.fset(self, value)

    async def get_hysteresis_temperature_async(self) -> int:
        return ADT7410.hysteresis_temperature.fget(self)

    async def set_hysteresis_temperature_async(self, value: int) -> None:
        ADT7410.hysteresis_temperature.fset(self, value)

# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
