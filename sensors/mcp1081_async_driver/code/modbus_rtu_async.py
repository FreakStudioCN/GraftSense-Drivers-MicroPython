# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : GraftSense Async Conversion
# @File    : modbus_rtu_async.py
# @Description : Asynchronous runtime helper
# @License : MIT

# ======================================== imports =============================================

"""Single-reader asynchronous Modbus RTU transport for MCP1081."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import Pin, UART


# ======================================== globals =============================================

DEFAULT_WAKE_DELAY_MS = 35


# ======================================== functions ===========================================

# ======================================== classes =============================================


class ModbusRTUMasterAsync:
    """Serialize complete Modbus RTU UART transactions for one master."""

    def __init__(self, pins, baudrate=9600, data_bits=8, stop_bits=1, parity=None, uart_id=0):
        self._uart = UART(uart_id, baudrate=baudrate, bits=data_bits, stop=stop_bits, parity=parity, tx=Pin(pins[0]), rx=Pin(pins[1]))
        self._lock = asyncio.Lock()
        self._closed = False

    async def wake_up_async(self, wake_delay_ms=DEFAULT_WAKE_DELAY_MS):
        if self._closed:
            raise RuntimeError("Modbus RTU master is closed")
        async with self._lock:
            self._uart.write(b"\x8f")
            await asyncio.sleep_ms(wake_delay_ms)
    async def transaction_async(self, frame, expected_size, timeout_ms, wake_delay_ms=DEFAULT_WAKE_DELAY_MS):
        """Send one framed request and return exactly one framed response."""
        if self._closed:
            raise RuntimeError("Modbus RTU master is closed")
        async with self._lock:
            while self._uart.any():
                self._uart.read()
            self._uart.write(b"\x8f")
            await asyncio.sleep_ms(wake_delay_ms)
            self._uart.write(frame)
            response = bytearray()
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            while len(response) < expected_size:
                if self._uart.any():
                    chunk = self._uart.read()
                    if chunk:
                        response.extend(chunk)
                        continue
                if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                    raise RuntimeError("MCP1081 Modbus response timeout")
                await asyncio.sleep_ms(2)
            if len(response) != expected_size:
                raise RuntimeError("MCP1081 Modbus response length mismatch")
            return response

    async def aclose(self):
        if not self._closed:
            self._closed = True
            deinit = getattr(self._uart, "deinit", None)
            if deinit is not None:
                deinit()
            self._uart = None

# ======================================== init ================================================

# ======================================== main ================================================
