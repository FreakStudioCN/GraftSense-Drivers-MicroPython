"""PMS7003 cooperative passive-mode UART driver."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
import struct

_HEADER = (0x42, 0x4D)
_ENTER_PASSIVE = bytes((0x42, 0x4D, 0xE1, 0x00, 0x00, 0x01, 0x70))
_ENTER_PASSIVE_REPLY = bytes((0x42, 0x4D, 0x00, 0x04, 0xE1, 0x00, 0x01, 0x74))
_SLEEP = bytes((0x42, 0x4D, 0xE4, 0x00, 0x00, 0x01, 0x73))
_SLEEP_REPLY = bytes((0x42, 0x4D, 0x00, 0x04, 0xE4, 0x00, 0x01, 0x77))
_WAKEUP = bytes((0x42, 0x4D, 0xE4, 0x00, 0x01, 0x01, 0x74))
_REQUEST_FRAME = bytes((0x42, 0x4D, 0xE2, 0x00, 0x00, 0x01, 0x71))


class Pms7003Async:
    """Single-reader passive PMS7003 protocol service."""
    def __init__(self, uart, poll_ms=5):
        if not hasattr(uart, "any") or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide any(), read(), and write()")
        self._uart = uart
        self._poll_ms = poll_ms
        self._buffer = bytearray()
        self._lock = asyncio.Lock()
        self._passive = False

    async def _receive(self, count, timeout_ms):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while len(self._buffer) < count:
            if self._uart.any():
                chunk = self._uart.read()
                if chunk:
                    self._buffer.extend(chunk)
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise RuntimeError("PMS7003 UART response timeout")
            await asyncio.sleep_ms(self._poll_ms)
        result = bytes(self._buffer[:count])
        del self._buffer[:count]
        return result

    async def _command(self, request, response=None, timeout_ms=1000):
        self._uart.write(request)
        await asyncio.sleep_ms(0)
        if response is not None:
            await asyncio.sleep_ms(2000)
            if await self._receive(len(response), timeout_ms) != response:
                raise RuntimeError("PMS7003 command response mismatch")

    async def enter_passive_async(self):
        async with self._lock:
            if not self._passive:
                self._buffer = bytearray()
                await self._command(_ENTER_PASSIVE, _ENTER_PASSIVE_REPLY)
                self._passive = True

    async def wakeup_async(self):
        async with self._lock:
            if not self._passive:
                raise RuntimeError("call enter_passive_async() before wakeup_async()")
            await self._command(_WAKEUP)

    async def read_async(self, timeout_ms=3000):
        async with self._lock:
            if not self._passive:
                raise RuntimeError("call enter_passive_async() before read_async()")
            await self._command(_REQUEST_FRAME)
            frame = await self._receive(32, timeout_ms)
            if frame[0] != _HEADER[0] or frame[1] != _HEADER[1]:
                raise RuntimeError("PMS7003 frame header mismatch")
            values = struct.unpack("!HHHHHHHHHHHHHBBH", frame[2:])
            if sum(frame[:30]) != values[15]:
                raise RuntimeError("PMS7003 frame checksum mismatch")
            keys = ("FRAME_LENGTH","PM1_0","PM2_5","PM10_0","PM1_0_ATM","PM2_5_ATM","PM10_0_ATM","PCNT_0_3","PCNT_0_5","PCNT_1_0","PCNT_2_5","PCNT_5_0","PCNT_10_0","VERSION","ERROR","CHECKSUM")
            return {keys[index]: values[index] for index in range(16)}

    async def sleep_async(self):
        async with self._lock:
            if self._passive:
                await self._command(_SLEEP, _SLEEP_REPLY)

    async def aclose(self):
        await asyncio.sleep_ms(0)