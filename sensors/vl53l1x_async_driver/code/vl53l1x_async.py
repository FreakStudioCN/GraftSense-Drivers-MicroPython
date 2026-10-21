# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : FreakStudio
# @File    : vl53l1x_async.py
# @Description : VL53L1X cooperative asynchronous lifecycle adapter
# @License : MIT

__version__ = "1.0.0"
__author__ = "FreakStudio"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from vl53l1x import VL53L1X, VL51L1X_DEFAULT_CONFIGURATION

# ======================================== 全局变量 ============================================

DEFAULT_TIMEOUT_MS = 1000

# ======================================== 功能函数 ============================================


async def _wait_ms_async(delay_ms, timeout_ms):
    started = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), started) < delay_ms:
        if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
            raise RuntimeError("VL53L1X initialization timeout")
        left = delay_ms - time.ticks_diff(time.ticks_ms(), started)
        await asyncio.sleep_ms(1 if left > 1 else left)


# ======================================== 自定义类 ============================================


class VL53L1XAsync(VL53L1X):
    """保留源寄存器协议的 VL53L1X 显式异步初始化适配器。"""

    def __init__(self, i2c, address=VL53L1X.I2C_DEFAULT_ADDR):
        if not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        self._i2c = i2c
        self._address = address
        self._initialized = False

    async def initialize_async(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        if self._initialized:
            return
        self.write_reg(0x0000, 0x00)
        await _wait_ms_async(100, timeout_ms)
        self.write_reg(0x0000, 0x01)
        if self.read_model_id() != 0xEACC:
            raise RuntimeError("Failed to find expected ID 0xEACC. Check wiring!")
        self._i2c.writeto_mem(
            self._address,
            0x2D,
            VL51L1X_DEFAULT_CONFIGURATION,
            addrsize=16,
        )
        self.write_reg_16bit(0x001E, self.read_reg_16bit(0x0022) * 4)
        await _wait_ms_async(200, timeout_ms)
        self._initialized = True

    async def read_async(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        if not self._initialized:
            raise RuntimeError("VL53L1X is not initialized")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        return self.read()

    async def aclose(self):
        self.deinit()
        self._initialized = False


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
