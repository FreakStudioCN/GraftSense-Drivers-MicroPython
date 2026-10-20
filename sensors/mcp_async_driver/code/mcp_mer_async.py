# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : GraftSense Async Conversion
# @File    : mer_async.py
# @Description : Asynchronous runtime helper
# @License : MIT

# ======================================== imports =============================================

import time
import uasyncio as asyncio
from machine import UART


# ======================================== globals =============================================

# ======================================== functions ===========================================

# ======================================== classes =============================================

class MERAsync:
    def __init__(self, slave_addr, uart_id, tx_pin, rx_pin, timeout_ms=500):
        self.slave_addr = slave_addr
        self._uart = UART(uart_id, baudrate=9600, bits=8, parity=None, stop=1, tx=tx_pin, rx=rx_pin)
        self._timeout_ms = timeout_ms
        self._lock = asyncio.Lock()
        self._closed = False

    @staticmethod
    def _crc(data):
        crc = 0xffff
        for byte in data:
            crc ^= byte
            for _ in range(8): crc = (crc >> 1) ^ 0xa001 if crc & 1 else crc >> 1
        return bytes((crc & 255, crc >> 8))

    async def _exchange(self, function, register, value=0, quantity=1):
        if self._closed:
            raise RuntimeError("MER is closed")
        async with self._lock:
            for _ in range(32):
                if not self._uart.any():
                    break
                self._uart.read()
                await asyncio.sleep_ms(0)
            request = bytes((self.slave_addr, function, register >> 8, register & 255,
                             (quantity if function == 3 else value) >> 8,
                             (quantity if function == 3 else value) & 255))
            self._uart.write(request + self._crc(request))
            expected = 5 + quantity * 2 if function == 3 else 8
            response, start = bytearray(), time.ticks_ms()
            while len(response) < expected:
                if self._uart.any():
                    data = self._uart.read()
                    if data: response.extend(data); continue
                if time.ticks_diff(time.ticks_ms(), start) >= self._timeout_ms: raise OSError('MER Modbus response timeout')
                await asyncio.sleep_ms(2)
            response = response[:expected]
            if response[-2:] != self._crc(response[:-2]): raise OSError('MER Modbus CRC mismatch')
            if response[0] != self.slave_addr or response[1] != function: raise ValueError('MER Modbus response mismatch')
            if function == 3:
                if response[2] != quantity * 2: raise ValueError('MER register length mismatch')
                return [(response[i] << 8) | response[i + 1] for i in range(3, 3 + response[2], 2)]
            if response[2:6] != request[2:6]: raise ValueError('MER write echo mismatch')
            return True

    async def _read(self, register, quantity=1):
        try: return await self._exchange(3, register, quantity=quantity)
        except (OSError, ValueError): return None
    async def _write(self, register, value):
        try: return await self._exchange(6, register, value=value)
        except (OSError, ValueError): return False
    async def _one(self, register):
        values = await self._read(register)
        return values[0] if values else None
    async def read_node_address_async(self): return await self._one(0x01)
    async def write_node_address_async(self, value): return await self._write(0x01, value) if 1 <= value <= 247 else False
    async def read_level_async(self): return await self._one(0x02)
    async def read_temp_async(self):
        value = await self._one(0x03); return round(value / 10.0, 1) if value is not None else None
    async def read_capacitance_async(self):
        value = await self._one(0x04); return round(value / 1000.0, 3) if value is not None else None
    async def read_ratio_async(self):
        value = await self._one(0x05); return round(value / 1000.0, 3) if value is not None else None
    async def read_frequency_async(self):
        value = await self._one(0x06); return round(value / 1000.0, 3) if value is not None else None
    async def read_filter_count_async(self): return await self._one(0x07)
    async def write_filter_count_async(self, value): return await self._write(0x07, value) if 1 <= value <= 100 else False
    async def read_calib_switch_async(self): return await self._one(0x0e)
    async def write_calib_switch_async(self, value): return await self._write(0x0e, value) if value in (0, 1, 2, 3) else False
    async def read_low_power_enable_async(self): return await self._one(0x0f)
    async def write_low_power_enable_async(self, value): return await self._write(0x0f, value) if value in (0, 1) else False
    async def _version(self, register):
        value = await self._one(register); return '{}.{}'.format(value >> 8, value & 255) if value is not None else None
    async def read_hw_version_async(self): return await self._version(0x17)
    async def read_fw_version_async(self): return await self._version(0x18)
    async def read_device_uid_async(self):
        values = await self._read(0x19, 6); return ''.join('{:04X}'.format(v) for v in values) if values else None
    async def read_ref_level1_async(self): return await self._one(0x26)
    async def write_ref_level1_async(self, value): return await self._write(0x26, value)
    async def read_ref_level2_async(self): return await self._one(0x27)
    async def write_ref_level2_async(self, value): return await self._write(0x27, value)
    async def read_ref_level3_async(self): return await self._one(0x28)
    async def write_ref_level3_async(self, value): return await self._write(0x28, value)
    async def aclose(self):
        """Release the UART after in-flight serialized transactions have completed."""
        async with self._lock:
            if self._closed:
                return
            self._closed = True
            deinit = getattr(self._uart, "deinit", None)
            if deinit is not None:
                deinit()
            self._uart = None

# ======================================== init ================================================

# ======================================== main ================================================
