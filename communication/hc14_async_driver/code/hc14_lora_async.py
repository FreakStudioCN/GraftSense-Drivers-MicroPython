# -*- coding: utf-8 -*-
# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time

# ======================================== 全局变量 ============================================
_PAYLOADS = {1: 40, 2: 40, 3: 80, 4: 80, 5: 160, 6: 160, 7: 250, 8: 250}
_BAUDS = (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================
class HC14_LoraAsync:
    """HC-14 async UART service: one reader task owns all UART reads."""
    def __init__(self, uart, baud: int = 9600, poll_ms: int = 5) -> None:
        if not hasattr(uart, "any") or not hasattr(uart, "read") or not hasattr(uart, "write"):
            raise ValueError("uart must provide any(), read(), and write()")
        if baud not in _BAUDS or not isinstance(poll_ms, int) or poll_ms < 1:
            raise ValueError("unsupported baud or poll_ms")
        self._uart, self.baud, self._poll_ms = uart, baud, poll_ms
        self.rate, self.power, self.channel = 3, 20, 28
        self._reader_task, self._running = None, False
        self._input, self._transaction_lock = bytearray(), asyncio.Lock()

    async def start(self) -> None:
        if not self._running:
            self._running = True
            self._reader_task = asyncio.create_task(self._reader())

    async def aclose(self) -> None:
        self._running = False
        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None
        await asyncio.sleep_ms(0)

    async def _reader(self) -> None:
        while self._running:
            if self._uart.any():
                chunk = self._uart.read()
                if chunk:
                    self._input.extend(chunk)
                await asyncio.sleep_ms(0)
            else:
                await asyncio.sleep_ms(self._poll_ms)

    async def _at_async(self, command: bytes, timeout_ms: int = 1000, min_lines: int = 1) -> tuple:
        async with self._transaction_lock:
            self._input = bytearray()
            response_buffer = bytearray()
            try:
                self._uart.write(command)
            except OSError as exc:
                return False, "send error: %s" % exc
            await asyncio.sleep_ms(50)
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                if self._input:
                    response_buffer.extend(self._input)
                    self._input = bytearray()
                    text = bytes(response_buffer).decode("utf-8").strip()
                    if text == "ORDER ERROR":
                        return False, text
                    if len([line for line in text.split("\r\n") if line]) >= min_lines:
                        return True, text
                await asyncio.sleep_ms(self._poll_ms)
            return False, "timeout"

    async def test_comm_async(self, timeout_ms: int = 1000) -> tuple:
        ok, response = await self._at_async(b"AT", timeout_ms)
        return (True, None) if ok and response == "OK" else (False, response)

    async def set_channel_async(self, channel: int, timeout_ms: int = 1000) -> tuple:
        if not isinstance(channel, int) or channel < 1 or channel > 50:
            return False, "invalid param"
        ok, response = await self._at_async(("AT+C%03d" % channel).encode(), timeout_ms)
        if ok: self.channel = channel
        return ok, response

    async def set_rate_async(self, rate: int, timeout_ms: int = 1000) -> tuple:
        if not isinstance(rate, int) or rate not in _PAYLOADS: return False, "invalid param"
        ok, response = await self._at_async(("AT+S%d" % rate).encode(), timeout_ms)
        if ok: self.rate = rate
        return ok, response

    async def set_power_async(self, power: int, timeout_ms: int = 1000) -> tuple:
        if not isinstance(power, int) or power < 6 or power > 20: return False, "invalid param"
        ok, response = await self._at_async(("AT+P%d" % power).encode(), timeout_ms)
        if ok: self.power = power
        return ok, response

    async def get_version_async(self, timeout_ms: int = 1000) -> tuple:
        return await self._at_async(b"AT+V?", timeout_ms)

    async def get_params_async(self, timeout_ms: int = 1000) -> tuple:
        ok, response = await self._at_async(b"AT+RX", timeout_ms, min_lines=4)
        if not ok: return ok, response
        values = [item.split(":", 1)[1] for item in response.split("\r\n") if ":" in item]
        if len(values) != 4: return False, "get params error"
        return True, {"baud": values[0], "channel": values[1], "rate": values[2], "power": values[3]}

    async def transparent_send_async(self, data: bytes, wait_between_packets_ms: int = 10) -> tuple:
        if not isinstance(data, bytes) or not isinstance(wait_between_packets_ms, int) or wait_between_packets_ms < 0:
            return False, "invalid param"
        size, packets = _PAYLOADS[self.rate], 0
        async with self._transaction_lock:
            for start in range(0, len(data), size):
                packet = data[start:start + size]
                try: written = self._uart.write(packet)
                except OSError as exc: return False, "send error: %s" % exc
                if written != len(packet): return False, "send error"
                packets += 1
                if start + size < len(data): await asyncio.sleep_ms(wait_between_packets_ms)
        return True, {"packets": packets, "bytes_sent": len(data)}

    async def transparent_recv_async(self, max_total_bytes: int = 1024, timeout_ms: int = 5000, quiet_ms: int = 2300) -> tuple:
        if min(max_total_bytes, timeout_ms, quiet_ms) < 1: raise ValueError("receive limits must be positive")
        started, last, result = time.ticks_ms(), time.ticks_ms(), bytearray()
        while time.ticks_diff(time.ticks_ms(), started) < timeout_ms:
            if self._input:
                result.extend(self._input); self._input = bytearray(); last = time.ticks_ms()
                if len(result) >= max_total_bytes: return True, bytes(result[:max_total_bytes])
            elif result and time.ticks_diff(time.ticks_ms(), last) >= quiet_ms:
                return True, bytes(result)
            await asyncio.sleep_ms(self._poll_ms)
        return (True, bytes(result)) if result else (False, "timeout")

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
