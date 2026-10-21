# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16
# @Author  : mimingxuan
# @File    : shtc3_async.py
# @Description : SHTC3 cooperative asynchronous temperature and humidity driver
# @License : MIT

__version__ = "1.0.0"
__author__ = "mimingxuan"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from _gs_shtc3_shtc3 import SHTC3, SHTC3Error

# ======================================== 全局变量 ============================================

DEFAULT_TIMEOUT_MS = 100

# ======================================== 功能函数 ============================================


async def _wait_delay_async(delay_ms, timeout_ms):
    """协作式等待固定转换时间，并使用 ticks 处理超时。"""
    started = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), started) < delay_ms:
        if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
            raise RuntimeError("SHTC3 conversion timeout")
        remaining = delay_ms - time.ticks_diff(time.ticks_ms(), started)
        await asyncio.sleep_ms(1 if remaining > 1 else remaining)


# ======================================== 自定义类 ============================================


class SHTC3Async(SHTC3):
    """SHTC3 的协作式异步适配器，保持原有命令、CRC 与换算语义。"""
    def __init__(self, i2c, addr=SHTC3.I2C_DEFAULT_ADDR, delta_temp=0.0, delta_hum=0.0, debug=False):
        if hasattr(i2c, "writeto") is False:
            raise ValueError("i2c must provide writeto")
        if not isinstance(addr, int) or not 0 <= addr <= 0x7F:
            raise ValueError("addr must be an I2C address from 0x00 to 0x7F")
        if not isinstance(delta_temp, (int, float)) or not isinstance(delta_hum, (int, float)):
            raise ValueError("deltas must be numeric")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._i2c = i2c
        self._addr = addr
        self._delta_temp = delta_temp
        self._delta_hum = delta_hum
        self._debug = debug

    async def initialize_async(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        """等待源构造期规定的上电稳定窗口。"""
        if timeout_ms < self.INIT_DELAY_MS:
            raise RuntimeError("SHTC3 initialization timeout")
        await _wait_delay_async(self.INIT_DELAY_MS, timeout_ms)

    async def reset_async(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        """保留唤醒命令与 240us 严格时序，仅转换复位后的毫秒等待。"""
        self.wakeup()
        self._write_cmd(self.RESET_CMD)
        await _wait_delay_async(self.RESET_DELAY_MS, timeout_ms)

    async def _send_cmd_async(self, cmd, response_size, read_delay_ms, timeout_ms):
        self._write_cmd(cmd)
        await _wait_delay_async(read_delay_ms, timeout_ms)
        try:
            data = self._i2c.readfrom(self._addr, response_size)
        except OSError as error:
            raise SHTC3Error(SHTC3Error.BUS_ERROR) from error
        if data == bytearray(response_size):
            raise SHTC3Error(SHTC3Error.DATA_ERROR)
        for index in range(response_size // 3):
            chunk = data[index * 3 : (index + 1) * 3]
            if not self._check_crc(chunk):
                raise SHTC3Error(SHTC3Error.CRC_ERROR)
        return data

    async def read_id_async(self, timeout_ms=DEFAULT_TIMEOUT_MS):
        self.wakeup()
        try:
            data = await self._send_cmd_async(
                self.READ_ID_CMD,
                3,
                self.READ_ID_DELAY_MS,
                timeout_ms,
            )
            return (data[0] << 8) | data[1]
        finally:
            self.sleep()

    async def measure_async(
        self,
        raw=False,
        low_power=False,
        rh_first=False,
        timeout_ms=DEFAULT_TIMEOUT_MS,
    ):
        if not isinstance(raw, bool):
            raise ValueError("raw must be bool")
        if not isinstance(low_power, bool):
            raise ValueError("low_power must be bool")
        if not isinstance(rh_first, bool):
            raise ValueError("rh_first must be bool")
        if low_power:
            cmd = self.MEASURE_LOW_POWER_RH_FIRST_CMD if rh_first else self.MEASURE_LOW_POWER_T_FIRST_CMD
            delay_ms = self.LOW_POWER_MEASURE_DELAY_MS
        else:
            cmd = self.MEASURE_NORMAL_RH_FIRST_CMD if rh_first else self.MEASURE_NORMAL_T_FIRST_CMD
            delay_ms = self.NORMAL_MEASURE_DELAY_MS
        self.wakeup()
        try:
            data = await self._send_cmd_async(cmd, 6, delay_ms, timeout_ms)
        finally:
            self.sleep()
        if raw:
            return data
        if rh_first:
            raw_rh = (data[0] << 8) | data[1]
            raw_temp = (data[3] << 8) | data[4]
        else:
            raw_temp = (data[0] << 8) | data[1]
            raw_rh = (data[3] << 8) | data[4]
        temperature = self.TEMP_MIN_C + (self.TEMP_SCALE * raw_temp / self.RAW_MAX) + self._delta_temp
        humidity = (self.HUM_SCALE * raw_rh / self.RAW_MAX) + self._delta_hum
        return temperature, min(100, max(0, humidity))

    async def measure_int_async(self, low_power=False, timeout_ms=DEFAULT_TIMEOUT_MS):
        temperature, humidity = await self.measure_async(
            low_power=low_power,
            timeout_ms=timeout_ms,
        )
        t_int = int(temperature)
        t_dec = int(abs(temperature - t_int) * 100)
        h_int = int(humidity)
        h_dec = int((humidity - h_int) * 100)
        return t_int, t_dec, h_int, h_dec

    async def aclose(self):
        self.deinit()


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
