# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : bmi270_async.py
# @Description : Cooperative BMI270 lifecycle facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import _gs_bmi270_bmi270 as source

# ======================================== 全局变量 ============================================
_CONFIG_BLOCK_SIZE = 32
_CONFIG_BLOCKS = 256

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class BMI270(source.BMI270):
    """BMI270 facade preserving config-upload order while yielding between blocks."""

    async def initialize_async(self):
        if self.internal_status != 0x01:
            self._power_configuration = 0x00
            await asyncio.sleep_ms(1)
            self._init_control = 0x00
            for block in range(_CONFIG_BLOCKS):
                self._init_address_0 = 0x00
                self._init_address_1 = block
                await asyncio.sleep_ms(30)
                start = block * _CONFIG_BLOCK_SIZE
                try:
                    self._i2c.writeto_mem(self._address, 0x5E, bytes(source.bmi270_config_file[start:start + _CONFIG_BLOCK_SIZE]))
                except OSError as exc:
                    raise RuntimeError("Failed to write config file at block %d" % block) from exc
                await asyncio.sleep_ms(1)
            self._init_control = 0x01
            await asyncio.sleep_ms(20)
        self.power_control = 0x0E
        await asyncio.sleep_ms(100)
        self.power_config = 0x00
        await asyncio.sleep_ms(100)
        self.acceleration_range = source.ACCEL_RANGE_2G
        self.gyro_range = source.GYRO_RANGE_250
        self._initialized = True

    async def error_code_async(self):
        return source.BMI270.error_code(self)

    async def soft_reset_async(self):
        self._soft_reset = source.RESET_COMMAND
        await asyncio.sleep_ms(15)
        self._initialized = False

    async def aclose(self):
        source.BMI270.deinit(self)
        self._initialized = False

# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================