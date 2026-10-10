"""Single-reader, timeout-bounded CH9121 transport facade."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from ch9121_core import CH9121 as _CH9121


class CH9121Async(_CH9121):
    """Serialize configuration and transparent UART traffic through one reader."""

    def __init__(self, uart, cfg):
        if not all(hasattr(uart, name) for name in ("any", "read", "write")):
            raise TypeError("uart must provide any(), read(), and write()")
        if not hasattr(cfg, "value"):
            raise TypeError("cfg must provide value()")
        self.uart = uart
        self.cfg = cfg
        self._uart_lock = asyncio.Lock()
        self._closed = False

    async def _read_uart_async(self, size, timeout_ms):
        started = time.ticks_ms()
        while self.uart.any() == 0:
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                raise TimeoutError("CH9121 read timed out")
            await asyncio.sleep_ms(10)
        return self.uart.read(min(size, self.uart.any()))

    async def _config(self, cmd, n=1, timeout_ms=1500):
        async with self._uart_lock:
            self.cfg.value(0)
            try:
                self.uart.write(b"\x57\xab" + cmd)
                response = bytearray()
                started = time.ticks_ms()
                while len(response) < n:
                    if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                        raise TimeoutError("CH9121 configuration response timed out")
                    if self.uart.any():
                        remaining = timeout_ms - time.ticks_diff(time.ticks_ms(), started)
                        chunk = await self._read_uart_async(n - len(response), remaining)
                        if chunk:
                            response.extend(chunk)
                            continue
                    await asyncio.sleep_ms(10)
                return bytes(response)
            finally:
                self.cfg.value(1)

    async def reset(self):
        """Source reset byte through the same single UART writer and lock."""
        async with self._uart_lock:
            if self._closed:
                raise RuntimeError("CH9121 is closed")
            return self.uart.write(b"\x57\xab\x02")
    async def read_async(self, n, timeout_ms=1500):
        if not isinstance(n, int) or n < 1:
            raise ValueError("n must be >= 1")
        async with self._uart_lock:
            return await self._read_uart_async(n, timeout_ms)

    async def read(self, n):
        return await self.read_async(n)

    async def readline(self, timeout_ms=1500, max_bytes=1024):
        result = bytearray()
        started = time.ticks_ms()
        async with self._uart_lock:
            while len(result) < max_bytes:
                remaining = timeout_ms - time.ticks_diff(time.ticks_ms(), started)
                if remaining <= 0:
                    raise TimeoutError("CH9121 readline timed out")
                chunk = await self._read_uart_async(1, remaining)
                result.extend(chunk)
                if chunk == b"\n":
                    break
        return bytes(result)

    async def write_async(self, data):
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        async with self._uart_lock:
            return self.uart.write(data)

    async def write(self, data):
        return await self.write_async(data)

    async def deinit(self):
        async with self._uart_lock:
            self._closed = True
            self.cfg.value(1)

    async def aclose(self):
        await self.deinit()