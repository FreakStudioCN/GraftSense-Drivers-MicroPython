
# Preserve the documented exception contract on MicroPython.
try:
    TimeoutError
except NameError:
    try:
        from uasyncio import TimeoutError
    except ImportError:
        from asyncio import TimeoutError

# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Mike Causer
# @File    : hdc1080_async.py
# @Description : Source-faithful asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
import _gs_hdc1080_hdc1080 as hdc1080

REG_TEMPERATURE = 0x00
REG_HUMIDITY = 0x01
REG_CONFIG = 0x02
REG_SERIAL_ID0 = 0xFB
REG_SERIAL_ID1 = 0xFC
REG_SERIAL_ID2 = 0xFD
REG_MANUFACTURER_ID = 0xFE
REG_DEVICE_ID = 0xFF


# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class HDC1080Async(hdc1080.HDC1080):
    """HDC1080 with source-faithful cooperative conversion waits."""

    async def _read16_async(self, reg, timeout_ms=50):
        if not isinstance(reg, int) or not 0 <= reg <= 0xFF:
            raise ValueError("reg must be a register from 0x00 to 0xFF")
        started = time.ticks_ms()
        try:
            self._buf1[0] = reg
            self._i2c.writeto(self._addr, self._buf1)
            await asyncio.sleep_ms(20)
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise TimeoutError("HDC1080 conversion timeout")
            self._i2c.readfrom_into(self._addr, self._buf2)
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % reg) from error
        return (self._buf2[0] << 8) | self._buf2[1]

    async def temperature_async(self, timeout_ms=50):
        return (await self._read16_async(REG_TEMPERATURE, timeout_ms)) / 65536 * 165 - 40

    async def humidity_async(self, timeout_ms=50):
        return (await self._read16_async(REG_HUMIDITY, timeout_ms)) / 65536 * 100

    async def device_id_async(self, timeout_ms=50):
        return await self._read16_async(REG_DEVICE_ID, timeout_ms)

    async def serial_number_async(self, timeout_ms=50):
        first = await self._read16_async(REG_SERIAL_ID0, timeout_ms)
        second = await self._read16_async(REG_SERIAL_ID1, timeout_ms)
        third = await self._read16_async(REG_SERIAL_ID2, timeout_ms)
        return (first << 24) | (second << 8) | (third >> 8)

    async def check_async(self):
        return self.check()

    async def config_async(self, config=None, humid_res=None, temp_res=None, mode=None, heater=None):
        if config is not None and not isinstance(config, int):
            raise ValueError("config must be int")
        if humid_res is not None and not isinstance(humid_res, int):
            raise ValueError("humid_res must be int")
        if temp_res is not None and not isinstance(temp_res, int):
            raise ValueError("temp_res must be int")
        if mode is not None and not isinstance(mode, int):
            raise ValueError("mode must be int")
        if heater is not None and not isinstance(heater, bool):
            raise ValueError("heater must be bool")
        if config is not None:
            self._config = config
            self._write_config()
            return
        self._config = (await self._read16_async(REG_CONFIG)) >> 8
        if humid_res is not None:
            if humid_res == 8:
                self._config |= 2
                self._config &= ~1
            elif humid_res == 11:
                self._config &= ~2
                self._config |= 1
            elif humid_res == 14:
                self._config &= ~3
            else:
                raise ValueError("humid_res must be 8, 11 or 14")
        if temp_res is not None:
            if temp_res == 11:
                self._config |= 4
            elif temp_res == 14:
                self._config &= ~4
            else:
                raise ValueError("temp_res must be 11 or 14")
        if mode is not None:
            self._config &= ~16
            self._config |= (mode & 1) << 4
        if heater is not None:
            self._config &= ~32
            self._config |= (heater & 1) << 5
        self._write_config()

    async def reset_async(self, timeout_ms=50):
        self._config = 128
        self._write_config()
        self._config = (await self._read16_async(REG_CONFIG, timeout_ms)) >> 8

    async def battery_status_async(self, timeout_ms=50):
        self._config = (await self._read16_async(REG_CONFIG, timeout_ms)) >> 8
        return (self._config >> 3) & 1

    async def manufacturer_id_async(self, timeout_ms=50):
        return await self._read16_async(REG_MANUFACTURER_ID, timeout_ms)

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
