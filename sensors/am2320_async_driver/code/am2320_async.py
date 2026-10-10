# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Mike Causer
# @File    : am2320_async.py
# @Description : Source-faithful asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from am2320 import AM2320, _crc16


# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================

class AM2320Async(AM2320):
    async def _wake_async(self, timeout_ms=50):
        started = time.ticks_ms()
        try:
            self._i2c.writeto(self._addr, b"")
        except OSError:
            pass
        await asyncio.sleep_ms(10)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("AM2320 wake timeout")

    async def measure_async(self, retries=1, delay_ms=5, timeout_ms=200):
        if not isinstance(retries, int):
            raise ValueError("retries must be int")
        if retries < 0:
            raise ValueError("retries must be >= 0")
        if not isinstance(delay_ms, int):
            raise ValueError("delay_ms must be int")
        if delay_ms < 0:
            raise ValueError("delay_ms must be >= 0")
        started = time.ticks_ms()
        await self._wake_async(timeout_ms=timeout_ms)
        buf = self._buf
        for attempt in range(retries + 1):
            if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
                raise RuntimeError("AM2320 measurement timeout")
            try:
                self._i2c.writeto(self._addr, b"\x03\x00\x04")
                await asyncio.sleep_ms(2)
                if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
                    raise RuntimeError("AM2320 measurement timeout")
                self._i2c.readfrom_into(self._addr, buf)
                break
            except OSError as error:
                if attempt == retries:
                    raise RuntimeError(
                        "AM2320 I2C read failed after %d retries" % retries
                    ) from error
                await asyncio.sleep_ms(delay_ms)
        crc = buf[6] | (buf[7] << 8)
        if crc != _crc16(buf[:-2]):
            raise ValueError("AM2320 CRC checksum error")
        self._log("measure OK: raw=%s" % buf.hex())

    def temperature(self):
        return super().temperature()

    def humidity(self):
        return super().humidity()
    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
