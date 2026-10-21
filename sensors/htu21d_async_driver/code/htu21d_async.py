# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Julian Hille
# @File    : htu21d_async.py
# @Description : HTU21D asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from htu21d import HTU21D, _BUF3, _crc_check


# ======================================== 全局变量 ============================================
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class HTU21DAsync(HTU21D):
    async def _issue_measurement_async(self, cmd, timeout_ms=200):
        if not isinstance(cmd, int) or not 0 <= cmd <= 0xFFFF:
            raise ValueError("cmd must be an integer command value")
        delay_ms = 60 if cmd in (0xE3, 0xF3) else 30 if cmd in (0xE5, 0xF5) else 60
        if not isinstance(timeout_ms, int) or timeout_ms < delay_ms:
            raise ValueError("timeout_ms must cover measurement delay")
        started = time.ticks_ms()
        self._log("measuring cmd=0x%02X delay=%dms" % (cmd, delay_ms))
        for attempt in range(3):
            try:
                self._i2c.writeto(self._addr, bytes([cmd]))
                break
            except OSError as error:
                if attempt == 2:
                    raise RuntimeError("HTU21D I2C write failed for cmd 0x%02X" % cmd) from error
                await asyncio.sleep_ms(5)
        await asyncio.sleep_ms(delay_ms)
        if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
            raise RuntimeError("HTU21D measurement timeout")
        for attempt in range(5):
            try:
                self._i2c.readfrom_into(self._addr, _BUF3)
                break
            except OSError as error:
                if attempt == 4:
                    raise RuntimeError("HTU21D I2C read failed for cmd 0x%02X" % cmd) from error
                await asyncio.sleep_ms(5)
        if not _crc_check(_BUF3):
            raise RuntimeError("HTU21D CRC check failed for cmd 0x%02X" % cmd)
        return ((_BUF3[0] << 8) | _BUF3[1]) & 0xFFFC

    async def temperature_async(self, timeout_ms=200):
        return -46.85 + (175.72 * (await self._issue_measurement_async(self.ISSUE_TEMP_ADDRESS, timeout_ms)) / 65536)

    async def humidity_async(self, timeout_ms=200):
        return -6.0 + (125.0 * (await self._issue_measurement_async(self.ISSUE_HU_ADDRESS, timeout_ms)) / 65536)

    async def aclose(self):
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
