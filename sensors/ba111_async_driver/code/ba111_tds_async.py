# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : hogeiha
# @File    : ba111_tds_async.py
# @Description : Asynchronous driver facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
import ba111_tds

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================
class BA111TDSAsync(ba111_tds.BA111TDS):
    """Single-reader UART implementation of the source BA111 transaction protocol."""

    def __init__(self, uart):
        super().__init__(uart)
        self._transaction_lock = asyncio.Lock()
        self._closed = False

    def _read_uart(self, count=None):
        """The only UART read primitive; async callers are serialized by _transaction_lock."""
        if count is None:
            return self._uart.read()
        return self._uart.read(count)
    async def _drain_input_async(self, timeout_ms=100):
        started = time.ticks_ms()
        while self._uart.any():
            self._read_uart()
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise TimeoutError("BA111 UART input drain timeout")
            await asyncio.sleep_ms(0)

    async def _send_and_receive_async(self, frame, response_length=6, timeout_ms=None):
        if self._closed:
            raise RuntimeError("BA111TDSAsync is closed")
        if timeout_ms is None:
            timeout_ms = self._timeout
        async with self._transaction_lock:
            await self._drain_input_async()
            await asyncio.sleep_ms(50)
            self._uart.write(frame)
            started = time.ticks_ms()
            response = bytearray()
            while len(response) < response_length:
                if time.ticks_diff(time.ticks_ms(), started) > timeout_ms:
                    return None
                if self._uart.any():
                    data = self._read_uart(1)
                    if data:
                        response.append(data[0])
                await asyncio.sleep_ms(10)
            return bytes(response)

    async def detect_async(self, timeout_ms=None):
        response = await self._send_and_receive_async(
            self._build_frame(self.READ_TDS_TEMPERATURE),
            timeout_ms=timeout_ms,
        )
        if not response or response[0] != 0xAA or not self._validate_crc(response):
            return None
        tds_value = float((response[1] << 8) | response[2])
        self.tds_value = tds_value
        print(tds_value)
        temp_value = float((response[3] << 8) | response[4]) / 100.0
        self.temperature = temp_value
        print(temp_value)
        return tds_value, temp_value

    async def calibrate_async(self, calibration_confirmed, timeout_ms=None):
        """Calibrate only after the application explicitly confirms source conditions."""
        if calibration_confirmed is not True:
            raise ValueError("application must explicitly confirm pure water at 25C +/- 5C")
        response = await self._send_and_receive_async(
            self._build_frame(self.BASELINE_CALIBRATION),
            timeout_ms=timeout_ms,
        )
        if not response or len(response) < 6:
            return False
        if response == self.SUCCESS_RESPONSE:
            return True
        if response[0] == self.ERROR_RESPONSE_PREFIX[0] and response[5] == self.ERROR_RESPONSE_SUFFIX[3]:
            error_code = response[1]
            if error_code in self.ERROR_CODES:
                print("Calibration failed: %s" % self.ERROR_CODES[error_code])
            else:
                print("Calibration failed: Unknown error code 0x%02X" % error_code)
        return False

    async def set_ntc_resistance_async(self, resistance, timeout_ms=None):
        if resistance < 0 or resistance > 0xFFFFFFFF:
            print("Resistance value %sΩ out of range" % resistance)
            return False
        parameters = bytes([(resistance >> 24) & 0xFF, (resistance >> 16) & 0xFF, (resistance >> 8) & 0xFF, resistance & 0xFF])
        response = await self._send_and_receive_async(self._build_frame(self.SET_NTC_RESISTANCE, parameters), timeout_ms=timeout_ms)
        if response == self.SUCCESS_RESPONSE:
            self.ntc_resistance = resistance
            return True
        return False

    async def set_ntc_b_value_async(self, b_value, timeout_ms=None):
        if b_value < 0 or b_value > 0xFFFF:
            print("B value %s is out of range" % b_value)
            return False
        parameters = bytes([(b_value >> 8) & 0xFF, b_value & 0xFF, 0x00, 0x00])
        response = await self._send_and_receive_async(self._build_frame(self.SET_NTC_B, parameters), timeout_ms=timeout_ms)
        if response == self.SUCCESS_RESPONSE:
            self.ntc_b_value = b_value
            return True
        return False

    async def aclose(self):
        self._closed = True
        await asyncio.sleep_ms(0)
# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================
