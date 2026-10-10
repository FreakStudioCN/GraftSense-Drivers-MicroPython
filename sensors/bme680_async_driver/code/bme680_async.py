# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Pimoroni Ltd
# @File    : bme680_async.py
# @Description : Cooperative BME680 async facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import struct
import time
import bme680 as source

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class BME680_I2CAsync(source.BME680_I2C):
    """BME680 source driver with cooperative conversion polling."""

    async def initialize_async(self):
        await asyncio.sleep_ms(5)

    async def read_async(self, timeout_ms=1000):
        expired = time.ticks_diff(self._last_reading, time.ticks_ms()) * time.ticks_diff(0, 1)
        if 0 <= expired < self._min_refresh_time:
            await asyncio.sleep_ms(self._min_refresh_time - expired)
        self._write(source._BME680_REG_CONFIG, [self._filter << 2])
        self._write(source._BME680_REG_CTRL_MEAS, [(self._temp_oversample << 5) | (self._pressure_oversample << 2)])
        self._write(source._BME680_REG_CTRL_HUM, [self._humidity_oversample])
        self._write(source._BME680_REG_CTRL_GAS, [source._BME680_RUNGAS])
        ctrl = self._read_byte(source._BME680_REG_CTRL_MEAS)
        self._write(source._BME680_REG_CTRL_MEAS, [(ctrl & 0xFC) | 0x01])
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            data = self._read(source._BME680_REG_MEAS_STATUS, 15)
            if data[0] & 0x80:
                break
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("BME680 measurement timeout")
            await asyncio.sleep_ms(5)
        self._last_reading = time.ticks_ms()
        self._adc_pres = source._read24(data[2:5]) / 16
        self._adc_temp = source._read24(data[5:8]) / 16
        self._adc_hum = struct.unpack(">H", bytes(data[8:10]))[0]
        self._adc_gas = int(struct.unpack(">H", bytes(data[13:15]))[0] / 64)
        self._gas_range = data[14] & 0x0F
        var1 = (self._adc_temp / 8) - (self._temp_calibration[0] * 2)
        var2 = (var1 * self._temp_calibration[1]) / 2048
        var3 = ((var1 / 2) * (var1 / 2)) / 4096
        var3 = (var3 * self._temp_calibration[2] * 16) / 16384
        self._t_fine = int(var2 + var3)

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
