try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

class SIM800SMSAsync:
    def __init__(self, uart):
        if not hasattr(uart, "any") or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide any, read and write")
        self._uart = uart
        self._lock = asyncio.Lock()

    async def command_async(self, command, timeout_ms=1000):
        async with self._lock:
            while self._uart.any():
                self._uart.read()
            self._uart.write(command + "\r\n")
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            chunks = []
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                if self._uart.any():
                    data = self._uart.read()
                    if data:
                        chunks.append(data)
                        response = b"".join(chunks)
                        if b"\r\nOK\r\n" in response or b"\r\nERROR\r\n" in response:
                            return response
                await asyncio.sleep_ms(10)
            raise RuntimeError("SIM800 response timeout")

    async def initialize_async(self, timeout_ms=1000):
        await self.command_async("AT", timeout_ms)
        await self.command_async("ATE0", timeout_ms)
        return await self.command_async("AT+CFUN=1", timeout_ms)

    async def get_phone_number_async(self, timeout_ms=1000):
        return await self.command_async("AT+CNUM", timeout_ms)

    async def get_manufacturer_async(self, timeout_ms=1000):
        return await self.command_async("AT+CGMI", timeout_ms)

    async def get_signal_quality_async(self, timeout_ms=1000):
        return await self.command_async("AT+CSQ", timeout_ms)

    async def get_serial_number_async(self, timeout_ms=1000):
        return await self.command_async("AT+GSN", timeout_ms)

    async def aclose(self):
        self._uart = None
