# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 10:30
# @Author  : hogeiha
# @File    : modbus_rtu_async.py
# @Description : FDE-Frost Modbus RTU asynchronous transport
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

# ======================================== 全局变量 ============================================
__version__ = "0.1.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"
READ_HOLDING_REGISTERS = 0x03
WRITE_SINGLE_REGISTER = 0x06
DEFAULT_TIMEOUT_MS = 2000

# ======================================== 功能函数 ============================================
def _crc16(frame: bytes) -> int:
    crc = 0xFFFF
    for value in frame:
        crc ^= value
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def _u16(data: bytes) -> int:
    return (data[0] << 8) | data[1]

def _s16(data: bytes) -> int:
    value = _u16(data)
    return value - 65536 if value >= 32768 else value

# ======================================== 自定义类 ============================================
class FDEFrostTransportAsync:
    """FDE-Frost 的单 UART 所有权、锁保护 Modbus RTU 驱动。"""
    __slots__ = ("_slave_addr", "_uart", "_lock", "_closed")

    def __init__(self, slave_addr: int, uart: object) -> None:
        if not isinstance(slave_addr, int) or slave_addr < 1 or slave_addr > 247:
            raise ValueError("slave_addr must be from 1 to 247")
        if not hasattr(uart, "any") or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide any, read and write")
        self._slave_addr = slave_addr
        self._uart = uart
        self._lock = asyncio.Lock()
        self._closed = False

    async def read_registers_async(self, slave_addr: int, starting_addr: int,
                                   register_qty: int, signed: bool = True,
                                   timeout_ms: int = DEFAULT_TIMEOUT_MS) -> bytes:
        del signed
        if not isinstance(starting_addr, int) or not 0 <= starting_addr <= 0xFFFF:
            raise ValueError("starting_addr must be from 0 to 65535")
        if not isinstance(register_qty, int) or not 1 <= register_qty <= 125:
            raise ValueError("register_qty must be from 1 to 125")
        payload = bytes((READ_HOLDING_REGISTERS, starting_addr >> 8, starting_addr & 0xFF,
                         register_qty >> 8, register_qty & 0xFF))
        return await self._transaction_async(slave_addr, payload, 5 + register_qty * 2, timeout_ms)

    async def get_temperature_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> float:
        return _s16(await self.read_registers_async(self._slave_addr, 0x07, 1, False, timeout_ms)) / 10.0

    async def get_rain_status_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> int:
        return _u16(await self.read_registers_async(self._slave_addr, 0x04, 1, False, timeout_ms))

    async def get_capacitance_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> float:
        return _u16(await self.read_registers_async(self._slave_addr, 0x08, 1, False, timeout_ms)) / 1000.0

    async def get_count0_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> int:
        return _u16(await self.read_registers_async(self._slave_addr, 0x09, 1, False, timeout_ms))

    async def get_node_address_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> int:
        return _u16(await self.read_registers_async(self._slave_addr, 0x02, 1, False, timeout_ms))

    async def get_calibration_value_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> float:
        return _u16(await self.read_registers_async(self._slave_addr, 0x0E, 1, False, timeout_ms)) / 1000.0

    async def get_alarm_threshold_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> int:
        return _u16(await self.read_registers_async(self._slave_addr, 0x0F, 1, False, timeout_ms))

    async def get_clear_threshold_async(self, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> int:
        return _u16(await self.read_registers_async(self._slave_addr, 0x10, 1, False, timeout_ms))

    async def set_calibration_async(self, value: int = None) -> bool:
        return await self._write_and_wait_async(0x0E, value)

    async def set_alarm_threshold_async(self, value: int = None) -> bool:
        return await self._write_and_wait_async(0x0F, value)

    async def set_clear_threshold_async(self, value: int = None) -> bool:
        return await self._write_and_wait_async(0x10, value)

    async def _write_and_wait_async(self, address: int, value: int) -> bool:
        if value is None:
            return False
        if not isinstance(value, int) or not 0 <= value <= 0xFFFF:
            raise ValueError("register value must be from 0 to 65535")
        payload = bytes((WRITE_SINGLE_REGISTER, address >> 8, address & 0xFF, value >> 8, value & 0xFF))
        await self._transaction_async(self._slave_addr, payload, 8, DEFAULT_TIMEOUT_MS)
        await asyncio.sleep_ms(200)
        return True

    async def _transaction_async(self, slave_addr: int, payload: bytes, expected_length: int,
                                 timeout_ms: int) -> bytes:
        if self._closed:
            raise RuntimeError("FDE-Frost is deinitialized")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        async with self._lock:
            self._drain_rx()
            adu = bytes((slave_addr,)) + payload
            crc = _crc16(adu)
            try:
                self._uart.write(adu + bytes((crc & 0xFF, crc >> 8)))
            except OSError as exc:
                raise RuntimeError("FDE-Frost UART write failed") from exc
            response = bytearray()
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            while len(response) < expected_length:
                if self._uart.any():
                    try:
                        chunk = self._uart.read()
                    except OSError as exc:
                        raise RuntimeError("FDE-Frost UART read failed") from exc
                    if chunk:
                        response.extend(chunk)
                        continue
                if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                    raise RuntimeError("FDE-Frost Modbus response timeout")
                await asyncio.sleep_ms(2)
            self._validate_response(response, slave_addr, payload[0], expected_length)
            if payload[0] == READ_HOLDING_REGISTERS:
                if response[2] != expected_length - 5:
                    raise RuntimeError("FDE-Frost Modbus byte count mismatch")
                return bytes(response[3:-2])
            return bytes(response[2:6])

    def _drain_rx(self) -> None:
        while self._uart.any():
            self._uart.read()

    def _validate_response(self, response: bytearray, slave_addr: int,
                           function_code: int, expected_length: int) -> None:
        if len(response) != expected_length:
            raise RuntimeError("FDE-Frost Modbus response length mismatch")
        if response[0] != slave_addr:
            raise RuntimeError("FDE-Frost Modbus slave address mismatch")
        if response[1] & 0x80:
            raise RuntimeError("FDE-Frost Modbus exception response")
        if response[1] != function_code:
            raise RuntimeError("FDE-Frost Modbus function mismatch")
        received_crc = response[-2] | (response[-1] << 8)
        if _crc16(response[:-2]) != received_crc:
            raise RuntimeError("FDE-Frost Modbus CRC mismatch")

    def deinit(self) -> None:
        self._closed = True

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
