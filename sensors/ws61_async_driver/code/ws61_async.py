"""Cooperative WS61 Modbus RTU asynchronous driver."""
# MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Description : Cooperative WS61 Modbus RTU driver.
# @License : MIT

# ======================================== 导入相关模块 =========================================
import time
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
from machine import UART
# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================
# ======================================== 自定义类 ============================================
class WS61WaterAsync:
    """Asynchronous WS61 driver; one instance owns one UART transaction stream."""

    def __init__(self, slave_addr, uart, timeout_ms=500):
        if not all(hasattr(uart, name) for name in ("any", "read", "write")):
            raise TypeError("uart must provide any(), read(), and write()")
        self.slave_addr = slave_addr
        self.timeout_ms = timeout_ms
        self._uart = uart
        self._lock = asyncio.Lock()

    @staticmethod
    def _crc16(data):
        crc = 0xFFFF
        for value in data:
            crc ^= value
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return bytes((crc & 0xFF, (crc >> 8) & 0xFF))

    async def _wake_up_async(self):
        self._uart.write(b"\x8f")
        await asyncio.sleep_ms(30)

    async def _receive_async(self, expected_length, drain=False):
        response = bytearray()
        if drain:
            while self._uart.any():
                self._uart.read()
            return response
        start = time.ticks_ms()
        while len(response) < expected_length:
            if self._uart.any():
                data = self._uart.read()
                if data:
                    response.extend(data)
                    continue
            if time.ticks_diff(time.ticks_ms(), start) >= self.timeout_ms:
                raise OSError("WS61 Modbus response timeout")
            await asyncio.sleep_ms(2)
        return response[:expected_length]

    async def _transaction_async(self, function_code, register, value=0, read=False):
        async with self._lock:
            await self._receive_async(0, drain=True)
            await self._wake_up_async()
            if read:
                request = bytes((self.slave_addr, function_code, register >> 8,
                                 register & 0xFF, 0, 1))
                expected_length = 7
            else:
                request = bytes((self.slave_addr, function_code, register >> 8,
                                 register & 0xFF, value >> 8, value & 0xFF))
                expected_length = 8
            request += self._crc16(request)
            self._uart.write(request)
            response = await self._receive_async(expected_length)
            if response[-2:] != self._crc16(response[:-2]):
                raise OSError("WS61 Modbus CRC mismatch")
            if response[0] != self.slave_addr or response[1] == (function_code | 0x80):
                raise ValueError("WS61 Modbus exception")
            if response[1] != function_code:
                raise ValueError("WS61 Modbus function mismatch")
            if read:
                if response[2] != 2:
                    raise ValueError("WS61 Modbus register length mismatch")
                return (response[3] << 8) | response[4]
            if response[2:6] != request[2:6]:
                raise ValueError("WS61 Modbus write echo mismatch")
            return True

    async def _read_async(self, register, scale=1.0, digits=None):
        try:
            value = await self._transaction_async(3, register, read=True)
            if scale == 1.0:
                return value
            return round(value / scale, digits)
        except (OSError, ValueError):
            return None

    async def _write_async(self, register, value, settle_ms=0):
        try:
            await self._transaction_async(6, register, value)
            if settle_ms:
                await asyncio.sleep_ms(settle_ms)
            return True
        except (OSError, ValueError):
            return False

    async def read_device_id_async(self):
        return await self._read_async(0x01)

    async def write_device_id_async(self, dev_id):
        return await self._write_async(0x01, dev_id) if 1 <= dev_id <= 252 else False

    async def read_485_node_address_async(self):
        return await self._read_async(0x02)

    async def read_capacitance_async(self):
        return await self._read_async(0x12, 1000.0, 3)

    async def read_temperature_async(self):
        return await self._read_async(0x13, 10.0, 1)

    async def read_water_status_async(self):
        return await self._read_async(0x14)

    async def read_alarm_threshold_async(self):
        return await self._read_async(0x03, 1000.0, 3)

    async def write_alarm_threshold_async(self, threshold):
        value = int(threshold * 1000)
        return await self._write_async(0x03, value) if 0 <= value <= 65535 else False

    async def read_release_threshold_async(self):
        return await self._read_async(0x04, 1000.0, 3)

    async def write_release_threshold_async(self, threshold):
        value = int(threshold * 1000)
        return await self._write_async(0x04, value) if 0 <= value <= 65535 else False

    async def calibrate_sensor_async(self):
        return await self._write_async(0x07, 1, 500)

    def deinit(self):
        """Release this driver's reference; the caller owns the injected UART."""
        self._uart = None

    async def aclose(self):
        self.deinit()
# ======================================== 初始化配置 ===========================================
# ======================================== 主程序 ================================================
