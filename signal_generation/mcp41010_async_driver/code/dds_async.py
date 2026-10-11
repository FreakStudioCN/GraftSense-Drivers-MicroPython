# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/16 12:00
# @Author  : 李清水
# @File    : dds_async.py
# @Description : Async adapter for AD9833 and MCP41010
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

class AD9833Async:
    """Caller-owned AD9833 SPI transport with source-compatible frames."""
    def __init__(self, spi, cs, clk, fmclk=25):
        self._spi, self._cs, self._clk, self._fmclk = spi, cs, clk, fmclk * 1000000
        self._lock = asyncio.Lock()
        self._bits, self._write_mode = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], "BOTH"

    def _write(self, words):
        frame = bytearray()
        for word in words:
            frame.extend(((word >> 8) & 0xff, word & 0xff))
        self._clk.value(1)
        self._cs.value(0)
        try:
            self._spi.init(baudrate=1000000, polarity=0, phase=1)
            self._spi.write(frame)
        finally:
            self._cs.value(1)

    def _write_control(self):
        control = sum(bit << shift for bit, shift in zip(self._bits, (13, 12, 11, 10, 8, 7, 6, 5, 3, 1)))
        self._write((control,))

    async def initialize_async(self):
        """Emit the source constructor's B28/RESET control frame."""
        async with self._lock:
            self._bits = [1, 0, 0, 0, 1, 0, 0, 0, 0, 0]
            self._write_mode = "BOTH"
            self._write_control()

    async def write_data_async(self, data):
        if not 0 <= data <= 0xffff:
            raise ValueError("data must be a 16-bit word")
        async with self._lock:
            self._write((data,))

    async def set_control_reg_async(self, B28=1, HLB=0, FS=0, PS=0, RESET=0, SLP1=0, SLP12=0, OP=0, DIV2=0, MODE=0):
        bits = (B28, HLB, FS, PS, RESET, SLP1, SLP12, OP, DIV2, MODE)
        if any(bit not in (0, 1) for bit in bits):
            raise ValueError("control bits must be 0 or 1")
        async with self._lock:
            self._bits = list(bits)
            self._write_control()

    async def set_frequency_async(self, fout, freqSelect):
        if not 0 <= fout <= 12500000 or freqSelect not in (0, 1):
            raise ValueError("invalid frequency")
        async with self._lock:
            value, address = int(fout * (2 ** 28) / self._fmclk), (1 if freqSelect == 0 else 2) << 14
            words = (value & 0x3fff | address, (value >> 14) & 0x3fff | address)
            self._write(words[:1] if self._write_mode == "LSB" else words[1:] if self._write_mode == "MSB" else words)

    async def set_phase_async(self, pout, phaseSelect, rads=True):
        if phaseSelect not in (0, 1):
            raise ValueError("invalid phase select")
        if not rads:
            pout = pout * 3.141592653589793 / 180
        async with self._lock:
            self._write((int(pout * 4096 / (2 * 3.141592653589793)) | 0xc000 | (phaseSelect << 13),))

    async def set_mode_async(self, mode="SIN"):
        modes = {"SIN": (0, 0, 0, 0), "TRIANGLE": (0, 0, 0, 1), "SQUARE": (0, 1, 1, 0), "SQUARE/2": (0, 1, 0, 0), "RESET": (1, 0, 0, 0), "OFF": (1, 1, 1, 0)}
        if mode not in modes:
            raise ValueError("invalid mode")
        async with self._lock:
            self._bits[4], self._bits[6], self._bits[7], self._bits[9] = modes[mode]
            self._write_control()

    async def set_write_mode_async(self, writeMode="BOTH"):
        if writeMode not in ("BOTH", "MSB", "LSB"):
            raise ValueError("invalid write mode")
        async with self._lock:
            self._write_mode = writeMode
            self._bits[0], self._bits[1] = (1, 0) if writeMode == "BOTH" else (0, 1 if writeMode == "MSB" else 0)
            self._write_control()

    async def select_freq_phase_async(self, FS, PS):
        if FS not in (0, 1) or PS not in (0, 1):
            raise ValueError("frequency and phase selections must be 0 or 1")
        async with self._lock:
            self._bits[2], self._bits[3] = FS, PS
            self._write_control()

    async def aclose(self):
        return None

class MCP41010Async:
    """Caller-injected SPI adapter preserving MCP41010 command bytes."""
    def __init__(self, spi, cs, max_value=255):
        self._spi, self._cs, self._max_value = spi, cs, max_value
        self._lock = asyncio.Lock()

    def _send(self, command, data):
        self._cs.value(0)
        try:
            self._spi.init(baudrate=1000000, polarity=0, phase=0)
            self._spi.write(bytearray((command, data)))
        finally:
            self._cs.value(1)

    async def set_value_async(self, value):
        if value < 0 or value > self._max_value:
            raise ValueError("Value must be between 0 and %d" % self._max_value)
        async with self._lock:
            self._send(0x11, value)

    async def set_shutdown_async(self):
        async with self._lock:
            self._send(0x21, 0)

    async def aclose(self):
        return None


# ======================================== 自定义类 ============================================
class DDSAsync:
    def __init__(self, ad9833, mcp41010):
        self._lock = asyncio.Lock()
        self._ad9833 = ad9833
        self._mcp41010 = mcp41010
        self._closed = False

    async def initialize_async(self):
        async with self._lock:
            await self._ad9833.initialize_async()

    async def set_frequency_async(self, fout, freqSelect):
        async with self._lock:
            await self._ad9833.set_frequency_async(fout, freqSelect)

    async def set_phase_async(self, pout, phaseSelect, rads=True):
        async with self._lock:
            await self._ad9833.set_phase_async(pout, phaseSelect, rads)

    async def set_control_reg_async(self, B28=1, HLB=0, FS=0, PS=0, RESET=0, SLP1=0, SLP12=0, OP=0, DIV2=0, MODE=0):
        async with self._lock:
            await self._ad9833.set_control_reg_async(B28, HLB, FS, PS, RESET, SLP1, SLP12, OP, DIV2, MODE)

    async def set_write_mode_async(self, writeMode="BOTH"):
        async with self._lock:
            await self._ad9833.set_write_mode_async(writeMode)

    async def select_freq_phase_async(self, FS, PS):
        async with self._lock:
            await self._ad9833.select_freq_phase_async(FS, PS)

    async def set_mode_async(self, mode="SIN"):
        async with self._lock:
            await self._ad9833.set_mode_async(mode)

    async def set_value_async(self, value):
        async with self._lock:
            await self._mcp41010.set_value_async(value)

    async def set_shutdown_async(self):
        async with self._lock:
            await self._mcp41010.set_shutdown_async()

    async def aclose(self):
        if not self._closed:
            self._closed = True
            await self._ad9833.aclose()
            await self._mcp41010.aclose()

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
