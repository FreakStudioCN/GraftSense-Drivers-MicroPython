"""Single-reader, lock-serialized async CC253x UART protocol driver."""

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

from cc253x_ttl import CC253xTTL


class CC253xTTLAsync(CC253xTTL):
    PREFIX = b"\x02\xa8\x79\xc3"

    def __init__(self, uart, **kwargs):
        if not hasattr(uart, "read") or not hasattr(uart, "write") or not hasattr(uart, "any"):
            raise ValueError("uart must provide read, write, and any")
        super().__init__(uart, **kwargs)
        self._transaction_lock = asyncio.Lock()

    async def _read_available_async(self, timeout_ms=1000, drain=False):
        if drain:
            while self._uart.any():
                self._uart.read()
            return b""
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        chunks = []
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self._uart.any():
                data = self._uart.read()
                if data:
                    chunks.append(data)
                    await asyncio.sleep_ms(20)
                    if not self._uart.any():
                        return b"".join(chunks)
            await asyncio.sleep_ms(10)
        return b"".join(chunks)

    async def _command_async(self, command, timeout_ms=1000):
        async with self._transaction_lock:
            await self._read_available_async(drain=True)
            self._uart.write(self.PREFIX + bytes.fromhex(command))
            response = await self._read_available_async(timeout_ms)
            if len(response) < 5:
                return False, "No response from UART"
            tag = response[4]
            payload = response[5:].hex()
            if tag in (1, 5, 10, 11, 12, 14, 15):
                return True, payload
            if payload == "4f4b":
                return True, "success"
            if payload == "4552":
                return False, "failure"
            raise RuntimeError("CC253x command response is invalid")

    async def read_status_async(self, timeout_ms=1000):
        return (await self._command_async("01", timeout_ms))[1]

    async def read_panid_channel_async(self, timeout_ms=1000):
        response = (await self._command_async("05", timeout_ms))[1]
        return response[:4], response[4:]

    async def set_panid_async(self, panid, timeout_ms=1000):
        return (await self._command_async("02{:04X}".format(panid), timeout_ms))[0]

    async def set_channel_async(self, channel, timeout_ms=1000):
        return (await self._command_async("09{:02X}".format(channel), timeout_ms))[0]

    async def set_custom_short_addr_async(self, short_addr, timeout_ms=1000):
        return (await self._command_async("0D{:04X}".format(short_addr), timeout_ms))[0]

    async def send_coord_to_node_async(self, short_addr, data, timeout_ms=1000):
        command = "0B{:04X}{}".format(short_addr, data.encode("utf-8").hex())
        return (await self._command_async(command, timeout_ms))[0]

    async def send_node_to_coord_async(self, data, timeout_ms=1000):
        return (await self._command_async("0A" + data.encode("utf-8").hex(), timeout_ms))[0]

    async def send_node_to_node_async(self, source_addr, target_addr, data, timeout_ms=1000):
        command = "0F{:04X}{:04X}{}".format(source_addr, target_addr, data.encode("utf-8").hex())
        return (await self._command_async(command, timeout_ms))[0]

    async def send_transparent_async(self, data):
        async with self._transaction_lock:
            return self._uart.write(data)

    async def recv_frame_async(self, timeout_ms=1000):
        async with self._transaction_lock:
            data = await self._read_available_async(timeout_ms)
        if not data:
            return None, None, None, None
        if data[:4] != self.PREFIX:
            return "transparent", data, None, None
        command = data[4:5].hex()
        if command == "0f":
            return "node_to_node", data[9:], data[5:7].hex(), data[7:9].hex()
        if command == "0a":
            return "node_to_coord", data[7:], data[5:7].hex(), None
        if command == "0b":
            return "coord_to_node", data[5:], None, None
        raise RuntimeError("CC253x frame command is not supported")

    async def aclose(self):
        self._uart = None
