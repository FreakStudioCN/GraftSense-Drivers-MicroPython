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
import _gs_bme680_bme680 as source

# ======================================== 全局变量 ============================================
REG_CTRL_GAS = 0x71
REG_CTRL_HUM = 0x72
REG_CTRL_MEAS = 0x74
REG_CONFIG = 0x75
REG_MEAS_STATUS = 0x1D
RUNGAS = 0x10

# ======================================== 功能函数 ============================================


# ======================================== 自定义类 ============================================
class BME680_I2CAsync(source.BME680_I2C):
    """BME680 source driver with cooperative conversion polling."""

    def __init__(self, i2c, address=0x77, debug=False, *, refresh_rate=10):
        if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_mem_into"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int) or not 0 <= address <= 0x7F:
            raise ValueError("address must be an I2C address from 0x00 to 0x7F")
        if isinstance(debug, bool) is False:
            raise ValueError("debug must be bool")
        if isinstance(refresh_rate, bool) or not isinstance(refresh_rate, int) or refresh_rate <= 0:
            raise ValueError("refresh_rate must be a positive int")
        self._i2c = i2c
        self._address = address
        self._debug = debug
        self._refresh_rate = refresh_rate
        self._initialized = False
        self._async_sample_ready = False

    async def initialize_async(self):
        if self._initialized:
            return self
        self._write(0xE0, [0xB6])
        await asyncio.sleep_ms(5)
        if self._read_byte(0xD0) != 0x61:
            raise RuntimeError("Failed to find BME680! Chip ID mismatch")
        self._read_calibration()
        self._write(0x5A, [0x73])
        self._write(0x64, [0x65])
        self.sea_level_pressure = self._DEFAULT_SEA_LEVEL
        self._pressure_oversample = self._DEFAULT_PRESS_OS
        self._temp_oversample = self._DEFAULT_TEMP_OS
        self._humidity_oversample = self._DEFAULT_HUM_OS
        self._filter = self._DEFAULT_FILTER
        self._adc_pres = self._adc_temp = self._adc_hum = self._adc_gas = None
        self._gas_range = self._t_fine = None
        self._last_reading = time.ticks_ms()
        self._min_refresh_time = self._DEFAULT_REFRESH_MS // self._refresh_rate
        self._initialized = True
        return self

    def _perform_reading(self):
        if self._async_sample_ready:
            return
        return super()._perform_reading()

    async def read_async(self, timeout_ms=1000):
        if not self._initialized:
            raise RuntimeError("Call initialize_async() before read_async()")
        expired = time.ticks_diff(self._last_reading, time.ticks_ms()) * time.ticks_diff(0, 1)
        if 0 <= expired < self._min_refresh_time:
            await asyncio.sleep_ms(self._min_refresh_time - expired)
        self._write(REG_CONFIG, [self._filter << 2])
        self._write(REG_CTRL_MEAS, [(self._temp_oversample << 5) | (self._pressure_oversample << 2)])
        self._write(REG_CTRL_HUM, [self._humidity_oversample])
        self._write(REG_CTRL_GAS, [RUNGAS])
        ctrl = self._read_byte(REG_CTRL_MEAS)
        self._write(REG_CTRL_MEAS, [(ctrl & 0xFC) | 0x01])
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            data = self._read(REG_MEAS_STATUS, 15)
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

    async def measurements_async(self):
        await self.read_async()
        self._async_sample_ready = True
        try:
            return (
                self.temperature,
                self.humidity,
                self.pressure,
                self.gas,
                self.altitude,
            )
        finally:
            self._async_sample_ready = False

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ===========================================

# ======================================== 主程序 ==============================================
