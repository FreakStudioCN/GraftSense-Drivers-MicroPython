# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Tom Øyvind Hogstad
# @File    : ags02ma_async.py
# @Description : AGS02MA cooperative asynchronous facade
# @License : MIT
# @AsyncSafety : bounded I2C command/read transactions; no synchronous settling waits

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import struct
import time
import ags02ma
from ags02ma import AGS02MA

# ======================================== 全局变量 ============================================
_DEFAULT_DELAY_MS = 30
_DEFAULT_TIMEOUT_MS = 250
REG_TVOCSTAT = 0x00
REG_VERSION = 0x11
REG_GASRES = 0x20
READ_LENGTH = 5
READ_RETRIES = 3

def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.monotonic() * 1000)

def _ticks_add(base, delta):
    return time.ticks_add(base, delta) if hasattr(time, "ticks_add") else base + delta

def _ticks_diff(end, start):
    return time.ticks_diff(end, start) if hasattr(time, "ticks_diff") else end - start

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
_ASYNC_FACADE_P0 = True


class AGS02MAAsync(AGS02MA):
    """Source-faithful AGS02MA operations with cooperative command delays."""

    def __init__(self, i2c, addr=0x1A, debug=False):
        if not hasattr(i2c, "writeto"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(addr, int) or not 0x00 <= addr <= 0x7F:
            raise ValueError("addr must be int in range 0x00~0x7F, got %s" % addr)
        self._i2c = i2c
        self._addr = addr
        self._debug = debug
        self._initialized = False

    async def initialize_async(self, timeout_ms=_DEFAULT_TIMEOUT_MS):
        if not self._initialized:
            await self.firmware_version_async(timeout_ms)
            self._initialized = True
        return self

    async def _read_reg_async(self, addr: int, delayms: int = _DEFAULT_DELAY_MS,
                              retries: int = READ_RETRIES, timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> int:
        if not isinstance(addr, int) or not 0 <= addr <= 0xFF:
            raise ValueError("addr must be a register from 0x00 to 0xFF")
        if not isinstance(delayms, int) or delayms < 0:
            raise ValueError("delayms must be a non-negative int")
        if not isinstance(retries, int) or retries < 1:
            raise ValueError("retries must be a positive int")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        deadline = _ticks_add(_ticks_ms(), timeout_ms)
        last_data = None
        last_calc_crc = 0
        last_recv_crc = 0
        for _ in range(retries):
            if _ticks_diff(deadline, _ticks_ms()) <= 0:
                raise TimeoutError("AGS02MA operation timeout")
            try:
                self._i2c.writeto(self._addr, bytes([addr]))
            except OSError as error:
                raise RuntimeError("I2C write failed at reg 0x%02X" % addr) from error
            if _ticks_diff(deadline, _ticks_ms()) <= delayms:
                raise TimeoutError("AGS02MA operation timeout")
            await asyncio.sleep_ms(delayms)
            try:
                data = self._i2c.readfrom(self._addr, READ_LENGTH)
            except OSError as error:
                raise RuntimeError("I2C read failed at reg 0x%02X" % addr) from error
            last_data = data
            if self._is_invalid_frame(data):
                if _ticks_diff(deadline, _ticks_ms()) <= _DEFAULT_DELAY_MS:
                    raise TimeoutError("AGS02MA operation timeout")
                await asyncio.sleep_ms(_DEFAULT_DELAY_MS)
                continue
            last_calc_crc = ags02ma._crc8(data[:4])
            last_recv_crc = data[4]
            if last_calc_crc == last_recv_crc:
                value, _ = struct.unpack(">IB", data)
                self._log("reg 0x%02X = 0x%08X" % (addr, value))
                return value
            if _ticks_diff(deadline, _ticks_ms()) <= _DEFAULT_DELAY_MS:
                raise TimeoutError("AGS02MA operation timeout")
            await asyncio.sleep_ms(_DEFAULT_DELAY_MS)
        if last_data is None:
            last_data = bytearray()
        if self._is_invalid_frame(last_data):
            raise RuntimeError("Sensor data not ready reg 0x%02X data %s" % (addr, self._format_bytes(last_data)))
        raise RuntimeError("CRC check failed reg 0x%02X data %s calc 0x%02X recv 0x%02X" % (addr, self._format_bytes(last_data), last_calc_crc, last_recv_crc))

    async def firmware_version_async(self, timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> int:
        return await self._read_reg_async(REG_VERSION, self.DEFAULT_DELAY_MS, timeout_ms=timeout_ms)

    async def gas_resistance_async(self, timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> int:
        return (await self._read_reg_async(REG_GASRES, self.DEFAULT_DELAY_MS, timeout_ms=timeout_ms)) * 100

    async def TVOC_async(self, timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> int:
        value = await self._read_reg_async(REG_TVOCSTAT, self.DEFAULT_DELAY_MS, timeout_ms=timeout_ms)
        if (value >> 24) & 1:
            raise RuntimeError("Sensor still preheating")
        return value & 0xFFFFFF

    async def debug_read_raw_async(self, addr: int, delayms: int = _DEFAULT_DELAY_MS, timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> bytearray:
        if not isinstance(addr, int) or not 0 <= addr <= 0xFF:
            raise ValueError("addr must be a register from 0x00 to 0xFF")
        if not isinstance(delayms, int) or delayms < 0:
            raise ValueError("delayms must be a non-negative int")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        deadline = _ticks_add(_ticks_ms(), timeout_ms)
        if _ticks_diff(deadline, _ticks_ms()) <= 0:
            raise TimeoutError("AGS02MA operation timeout")
        try:
            self._i2c.writeto(self._addr, bytes([addr]))
            if _ticks_diff(deadline, _ticks_ms()) <= delayms:
                raise TimeoutError("AGS02MA operation timeout")
            await asyncio.sleep_ms(delayms)
            if _ticks_diff(deadline, _ticks_ms()) <= 0:
                raise TimeoutError("AGS02MA operation timeout")
            return self._i2c.readfrom(self._addr, READ_LENGTH)
        except OSError as error:
            raise RuntimeError("I2C read failed at reg 0x%02X" % addr) from error

    async def deinit_async(self) -> None:
        self.deinit()

    async def aclose(self) -> None:
        self.deinit()

# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
