# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : 缪贵成
# @File    : bmp280_float_async.py
# @Description : BMP280 cooperative forced-measurement facade
# @License : MIT
# @AsyncSafety : bounded status polling replaces source sleep loops

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from array import array
try:
    from time import ticks_ms, ticks_add, ticks_diff
except ImportError:
    import time
    ticks_ms = lambda: int(time.monotonic() * 1000)
    ticks_add = lambda base, delta: base + delta
    ticks_diff = lambda end, start: end - start
from bmp280_float import *

# ======================================== 全局变量 ============================================
_POLL_MS = 1
_DEFAULT_TIMEOUT_MS = 1005

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
_ASYNC_FACADE_P0 = True


class BMP280Async(BMP280):
    """BMP280 facade that preserves forced-mode protocol without blocking sleeps."""

    async def read_raw_data_async(self, result: object, timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> None:
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive int")
        deadline = ticks_add(ticks_ms(), timeout_ms)
        if ticks_diff(deadline, ticks_ms()) <= 0:
            raise TimeoutError("BMP280 conversion timeout")
        self._l1_barray[0] = self._mode_hum
        self.i2c.writeto_mem(self.address, BMP280_REGISTER_CONTROL_HUM, self._l1_barray)
        if ticks_diff(deadline, ticks_ms()) <= 0:
            raise TimeoutError("BMP280 conversion timeout")
        self._l1_barray[0] = self._mode_temp << 5 | self._mode_press << 2 | MODE_FORCED
        self.i2c.writeto_mem(self.address, BMP280_REGISTER_CONTROL, self._l1_barray)
        for _ in range(5):
            if ticks_diff(deadline, ticks_ms()) <= 0:
                raise TimeoutError("BMP280 conversion timeout")
            if self.i2c.readfrom_mem(self.address, BMP280_REGISTER_STATUS, 1)[0] & 0x08:
                break
            await asyncio.sleep_ms(_POLL_MS)
        while True:
            if ticks_diff(deadline, ticks_ms()) <= 0:
                raise TimeoutError("BMP280 conversion timeout")
            if self.i2c.readfrom_mem(self.address, BMP280_REGISTER_STATUS, 1)[0] & 0x08:
                await asyncio.sleep_ms(10)
            else:
                break
        else:
            raise RuntimeError("Sensor BMP280 not ready")
        if ticks_diff(deadline, ticks_ms()) <= 0:
            raise TimeoutError("BMP280 conversion timeout")
        self.i2c.readfrom_mem_into(self.address, 0xF7, self._l8_barray)
        readout = self._l8_barray
        result[0] = ((readout[3] << 16) | (readout[4] << 8) | readout[5]) >> 4
        result[1] = ((readout[0] << 16) | (readout[1] << 8) | readout[2]) >> 4
        result[2] = (readout[6] << 8) | readout[7]

    async def read_compensated_data_async(self, result: object = None, timeout_ms: int = _DEFAULT_TIMEOUT_MS) -> object:
        await self.read_raw_data_async(self._l3_resultarray, timeout_ms)
        raw_temp, raw_press, raw_hum = self._l3_resultarray
        var1 = (raw_temp / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = raw_temp / 131072.0 - self.dig_T1 / 8192.0
        var2 = var2 * var2 * self.dig_T3
        self.t_fine = int(var1 + var2)
        temp = max(-40, min(85, (var1 + var2) / 5120.0))
        var1 = (self.t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0.0:
            pressure = 30000
        else:
            pressure = ((1048576.0 - raw_press) - var2 / 4096.0) * 6250.0 / var1
            pressure += (self.dig_P9 * pressure * pressure / 2147483648.0 + pressure * self.dig_P8 / 32768.0 + self.dig_P7) / 16.0
            pressure = max(30000, min(110000, pressure))
        humidity = (raw_hum - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * self.t_fine)) * (self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * self.t_fine * (1.0 + self.dig_H3 / 67108864.0 * self.t_fine)))
        humidity *= 1.0 - self.dig_H1 * humidity / 524288.0
        humidity = max(0, min(100.0, humidity))
        if result is not None:
            result[0], result[1], result[2] = temp, pressure, humidity
            return result
        return array("f", (temp, pressure, humidity))

    async def aclose(self) -> None:
        deinit = getattr(self, "deinit", None)
        if deinit is not None:
            deinit()

# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
