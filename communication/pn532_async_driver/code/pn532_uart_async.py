try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from pn532 import MIFARE_CMD_AUTH_A


async def _pulse_low_async(pin, delay_ms):
    pin.value(0)
    started = time.ticks_ms()
    try:
        await asyncio.sleep_ms(delay_ms)
    finally:
        try:
            remaining = delay_ms - time.ticks_diff(time.ticks_ms(), started)
            while remaining > 0:
                try:
                    await asyncio.sleep_ms(remaining)
                except asyncio.CancelledError:
                    pass
                remaining = delay_ms - time.ticks_diff(time.ticks_ms(), started)
        finally:
            pin.value(1)


class PN532_UARTAsync:
    def __init__(self, uart, reset=None, debug=False):
        if not hasattr(uart, "any") or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide any, read and write")
        self._uart, self._reset, self._debug = uart, reset, debug
        self._lock = asyncio.Lock()
        self._rx = bytearray()

    def _read_uart_once(self):
        """The command lock makes this the sole UART receive primitive."""
        return self._uart.read()

    def _consume_frame(self):
        """Consume one validated frame from the persistent receive buffer."""
        invalid_frame = False
        while True:
            start = self._rx.find(b"\x00\x00\xff")
            if start < 0:
                if len(self._rx) > 2:
                    del self._rx[:-2]
                return None, invalid_frame
            if start:
                del self._rx[:start]
            if len(self._rx) < 5:
                return None, invalid_frame
            length, length_checksum = self._rx[3], self._rx[4]
            if length == 0:
                if len(self._rx) < 6:
                    return None, invalid_frame
                if self._rx[:6] == b"\x00\x00\xff\x00\xff\x00":
                    del self._rx[:6]
                    return b"", invalid_frame
                invalid_frame = True
                del self._rx[0]
                continue
            if (length + length_checksum) & 0xff:
                invalid_frame = True
                del self._rx[0]
                continue
            total = 7 + length
            if len(self._rx) < total:
                return None, invalid_frame
            payload = bytes(self._rx[5:5 + length])
            checksum, postamble = self._rx[5 + length], self._rx[6 + length]
            if postamble != 0 or (sum(payload) + checksum) & 0xff:
                invalid_frame = True
                del self._rx[0]
                continue
            del self._rx[:total]
            return payload, invalid_frame

    async def _read_frame_async(self, timeout_ms):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        invalid_frame = False
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            frame, was_invalid = self._consume_frame()
            invalid_frame = invalid_frame or was_invalid
            if frame is not None:
                return frame
            if self._uart.any():
                chunk = self._read_uart_once()
                if chunk:
                    self._rx.extend(chunk)
            await asyncio.sleep_ms(5)
        if invalid_frame:
            raise RuntimeError("PN532 response frame checksum is invalid")
        raise RuntimeError("PN532 response timeout")

    async def _command_async(self, command, params=b"", timeout_ms=1000):
        async with self._lock:
            while self._uart.any():
                self._read_uart_once()
            self._rx = bytearray()
            payload = bytes([0xD4, command]) + bytes(params)
            frame = b"\x00\x00\xff" + bytes([len(payload), (-len(payload)) & 0xff]) + payload
            frame += bytes([(-sum(payload)) & 0xff, 0x00])
            self._uart.write(frame)
            ack = await self._read_frame_async(timeout_ms)
            if ack:
                raise RuntimeError("PN532 ACK frame is invalid")
            response = await self._read_frame_async(timeout_ms)
            if len(response) < 2 or response[0] != 0xD5 or response[1] != ((command + 1) & 0xff):
                raise RuntimeError("PN532 response command mismatch")
            return response[2:]

    async def firmware_version_async(self, timeout_ms=500):
        return await self._command_async(0x02, timeout_ms=timeout_ms)

    async def SAM_configuration_async(self, timeout_ms=1000):
        return await self._command_async(0x14, b"\x01\x14\x01", timeout_ms)

    async def read_passive_target_async(self, timeout_ms=1000):
        response = await self._command_async(0x4A, b"\x01\x00", timeout_ms)
        if not response or response[0] != 1:
            return None
        if len(response) < 7 or response[5] > 7:
            raise RuntimeError("PN532 target response is invalid")
        return response[6:6 + response[5]]

    async def mifare_classic_authenticate_block_async(self, uid, block_num, key_type, key, timeout_ms=1000):
        response = await self._command_async(0x40, bytes([1, key_type, block_num]) + bytes(key) + bytes(uid), timeout_ms)
        return bool(response and response[0] == 0)

    async def mifare_classic_read_block_async(self, block_num, timeout_ms=1000):
        response = await self._command_async(0x40, bytes([1, 0x30, block_num]), timeout_ms)
        return response[1:] if response and response[0] == 0 else None

    async def mifare_classic_write_block_async(self, block_num, data, timeout_ms=1000):
        if len(data) != 16:
            raise ValueError("Mifare block data must be 16 bytes")
        response = await self._command_async(0x40, bytes([1, 0xA0, block_num]) + bytes(data), timeout_ms)
        return bool(response and response[0] == 0)

    async def power_down_async(self, timeout_ms=1000):
        response = await self._command_async(0x16, b"\xb0\x00", timeout_ms)
        return bool(response and response[0] == 0)

    async def reset_async(self):
        async with self._lock:
            if self._reset is not None:
                await _pulse_low_async(self._reset, 100)
                await asyncio.sleep_ms(100)
            self._uart.write(b"\x55" * 17)
            await asyncio.sleep_ms(10)

    async def aclose(self):
        async with self._lock:
            self._uart = None
