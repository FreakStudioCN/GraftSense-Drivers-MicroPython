"""Conservative async adapters for bounded synchronous bus calls."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from ch9328 import *

class SyncAdapterMixin:
    """Expose explicit async entry points without hiding bus blocking."""

    async def aclose(self):
        deinit = getattr(self, 'deinit', None)
        if deinit is not None:
            deinit()

class CH9328Async(SyncAdapterMixin, CH9328):
    """Async facade; each delegated call remains a short sync transaction."""

    def __init__(self, uart=UART):
        CH9328.__init__(self, uart)
        self._transaction_lock = asyncio.Lock()

    async def set_keyboard_mode_async(self, mode):
        if mode not in self.KEYBOARD_MODE:
            raise ValueError("无效工作模式，仅支持:%s" % self.KEYBOARD_MODE)
        self.current_mode = mode

    async def crlf_async(self):
        async with self._transaction_lock:
            return await self._crlf_unlocked()

    async def _crlf_unlocked(self):
        if self.current_mode not in (0, 2):
            return False
        self.uart.write(b"\x1b" if self.current_mode == 0 else b"\x28")
        await asyncio.sleep_ms(50)
        return True

    async def send_ascii_async(self, char):
        async with self._transaction_lock:
            return await self._send_ascii_unlocked(char)

    async def _send_ascii_unlocked(self, char):
        if self.current_mode == 3:
            return None
        if len(char) != 1:
            raise ValueError("send_ascii仅支持单个字符")
        if ord(char) not in range(0x20, 0x7F):
            raise ValueError("仅支持可见ASCII字符（空格~波浪号）")
        self.uart.write(char.encode("ascii"))
        await asyncio.sleep_ms(1)

    async def send_string_async(self, text):
        async with self._transaction_lock:
            if self.current_mode == 3:
                return None
            for char in text:
                await self._send_ascii_unlocked(char)
                await asyncio.sleep_ms(5)

    async def send_hid_packet_async(self, packet):
        async with self._transaction_lock:
            return await self._send_hid_packet_unlocked(packet)

    async def _send_hid_packet_unlocked(self, packet):
        if self.current_mode != 3 or len(packet) != 8:
            return False
        try:
            self.uart.write(packet)
            await asyncio.sleep_ms(1)
            return True
        except Exception:
            return False

    async def press_key_async(self, key_code, modifier=CH9328.MODIFIER_NONE):
        return await self.send_hid_packet_async(bytes((modifier, 0, key_code, 0, 0, 0, 0, 0)))

    async def release_key_async(self, key_code=None, modifier=CH9328.MODIFIER_NONE):
        return await self.send_hid_packet_async(b"\x00\x00\x00\x00\x00\x00\x00\x00")

    async def tap_key_async(self, key_code, modifier=CH9328.MODIFIER_NONE, delay=50):
        async with self._transaction_lock:
            await self._send_hid_packet_unlocked(bytes((modifier, 0, key_code, 0, 0, 0, 0, 0)))
            await asyncio.sleep_ms(delay)
            return await self._send_hid_packet_unlocked(b"\x00\x00\x00\x00\x00\x00\x00\x00")

    async def hotkey_async(self, modifier, key_code, delay=50):
        return await self.tap_key_async(key_code, modifier, delay)

    async def type_text_async(self, text, delay=10):
        async with self._transaction_lock:
            for char in text:
                if char not in self.CHAR_TO_HID:
                    continue
                modifier = self.MODIFIER_LEFT_SHIFT if char.isupper() else self.MODIFIER_NONE
                await self._send_hid_packet_unlocked(bytes((modifier, 0, self.CHAR_TO_HID[char], 0, 0, 0, 0, 0)))
                await asyncio.sleep_ms(delay)
                await self._send_hid_packet_unlocked(b"\x00\x00\x00\x00\x00\x00\x00\x00")
                await asyncio.sleep_ms(delay)
