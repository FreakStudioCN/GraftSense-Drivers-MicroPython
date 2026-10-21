# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : Jose D. Montoya
# @File    : hts221_async.py
# @Description : HTS221 asynchronous facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
"""Cooperative HTS221 API that preserves the source register protocol."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time

from _gs_hts221_hts221 import BDU_ENABLED, HTS221, RATE_12_5_HZ


# ======================================== 全局变量 ============================================
HTS221_CHIP_ID = 0xBC
WAIT_TIMEOUT_MS = 1000
WAIT_POLL_MS = 2

def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.monotonic() * 1000)

def _ticks_diff(end, start):
    return time.ticks_diff(end, start) if hasattr(time, "ticks_diff") else end - start
# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class HTS221Async(HTS221):
    """HTS221 facade with a cooperative one-shot conversion wait."""

    def __init__(self, i2c, address=0x5F, debug=False):
        """Store source-compatible configuration without running its blocking boot wait."""
        if not hasattr(i2c, "readfrom_mem"):
            raise ValueError("i2c must be an I2C instance")
        if not isinstance(address, int):
            raise ValueError("address must be int, got %s" % type(address))
        if address < 0 or address > 0x7F:
            raise ValueError("address must be 0~0x7F, got 0x%02X" % address)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))
        self._i2c = i2c
        self._address = address
        self._debug = debug

    async def initialize_async(self, timeout_ms=WAIT_TIMEOUT_MS):
        """Run the source startup, calibration and default-register sequence cooperatively."""
        try:
            chip_id = self._device_id
        except OSError as error:
            raise RuntimeError("Failed to communicate with HTS221 at 0x%02X" % self._address) from error
        if chip_id != HTS221_CHIP_ID:
            raise RuntimeError("Failed to find HTS221: expected 0x%02X, got 0x%02X" % (HTS221_CHIP_ID, chip_id))
        self._boot_bit = True
        started = _ticks_ms()
        while self._boot_bit:
            if _ticks_diff(_ticks_ms(), started) >= timeout_ms:
                raise RuntimeError("HTS221 boot timeout")
            await asyncio.sleep_ms(WAIT_POLL_MS)
        self.enabled = True
        self.data_rate = RATE_12_5_HZ
        self._block_data_update = BDU_ENABLED
        self._load_calibration()

    def _load_calibration(self):
        """Load calibration registers in the exact source order."""
        t1_t0_msbs = self._t1_t0_deg_c_x8_msbits
        self.calib_temp_value_0 = self._t0_deg_c_x8_lsbyte
        self.calib_temp_value_0 |= (t1_t0_msbs & 0b0011) << 8
        self.calibrated_value_1 = self._t1_deg_c_x8_lsbyte
        self.calibrated_value_1 |= (t1_t0_msbs & 0b1100) << 6
        self.calib_temp_value_0 >>= 3
        self.calibrated_value_1 >>= 3
        self.calib_temp_meas_0 = self._t0_out
        self.calib_temp_meas_1 = self._t1_out
        self.calib_hum_value_0 = self._h0_rh_x2
        self.calib_hum_value_0 >>= 1
        self.calib_hum_value_1 = self._h1_rh_x2
        self.calib_hum_value_1 >>= 1
        self.calib_hum_meas_0 = self._h0_t0_out
        self.calib_hum_meas_1 = self._h1_t1_out
    async def get_relative_humidity_async(self):
        """Return the source-calibrated relative humidity value."""
        return self.relative_humidity

    async def get_temperature_async(self):
        """Return the source-calibrated temperature value."""
        return self.temperature

    async def get_data_rate_async(self):
        """Return the source data-rate setting name."""
        return self.data_rate

    async def set_data_rate_async(self, value):
        """Set the source data-rate register field."""
        self.data_rate = value

    async def take_measurements_async(self, timeout_ms=WAIT_TIMEOUT_MS):
        """Trigger one-shot conversion using the source timeout and poll period."""
        self._one_shot_bit = True
        started = _ticks_ms()
        while self._one_shot_bit:
            if _ticks_diff(_ticks_ms(), started) >= timeout_ms:
                raise RuntimeError("HTS221 one-shot measurement timeout")
            await asyncio.sleep_ms(WAIT_POLL_MS)

    async def get_block_data_update_async(self):
        """Return the source block-data-update setting name."""
        return self.block_data_update

    async def set_block_data_update_async(self, value):
        """Set the source block-data-update register field."""
        self.block_data_update = value

    async def aclose(self):
        """Disable the sensor using the source shutdown sequence."""
        self.deinit()

# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ===============================================
